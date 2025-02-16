import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Awaitable, Callable, NamedTuple

from PIL import Image

from kfe.features.visionlmutils.janus.modeling_vlm import MultiModalityCausalLM
from kfe.features.visionlmutils.janus.processing_vlm import VLChatProcessor
from kfe.utils.log import logger
from kfe.utils.model_manager import ModelManager, ModelType
from kfe.utils.video_frames_extractor import (get_video_duration_seconds,
                                              get_video_frame_at_offset)


class VisionLMModel(NamedTuple):
    model: MultiModalityCausalLM
    chat_processor: VLChatProcessor

class VisionLMEngine:
    def __init__(self, model_manager: ModelManager, max_tokens=200, min_video_description_characters=70):
        self.model_manager = model_manager
        self.max_tokens = max_tokens
        self.min_video_description_characters = min_video_description_characters
        self.executor = ThreadPoolExecutor(max_workers=1)

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.VISION_LM):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.VISION_LM))

    @staticmethod
    def _get_image_description_prompt() -> str:
        return (
'''<image_placeholder>
Describe in around 3 sentences visual and semantic aspects of the image.
Rules:
- You must describe the meaning of the image (for example 'person driving a car' or 'meme showing a cat dressed like a man') and visual aspects of it, like colors, items or people on the foreground and backgroud, clothes, etc.
- If image depicts a person or a group of people you must also describe their emotions based on their facial expressions and gestures.
- Construct the description as follows: in the first sentence describe just the visuals, explain what is on the image. In the second sentence provide more details about depicted people or objects on the foregroud and background. In the third sentence write the general meaning of the image, try to guess what is happening there. 
Your description will be used as a part of search system and should cover aspects that people might want to search by.''')

    class Engine:
        def __init__(self, wrapper: "VisionLMEngine", lazy_model_provider: Callable[[], Awaitable[VisionLMModel]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def generate_image_description(self, image_path: Path) -> str:
            image = Image.open(image_path).convert('RGB')
            return await self._generate_image_description(image)
        
        async def generate_video_description(self, video_path: Path) -> str:
            # TODO maybe use some fast heuristic for selection, e.g., motion with unrecognizable objects
            # should have bad compression ratio, while static image with uniform-ish objects should
            # have better compression ratio, for now lets just assume that llm will produce short
            # output if it fails to recognize anything on the image and longer if it succeeds
            video_duration = await get_video_duration_seconds(video_path)
            initial_attempt = video_duration / 2
            frame = await get_video_frame_at_offset(video_path, initial_attempt)
            description = await self._generate_image_description(frame)
            if len(description) >= self.wrapper.min_video_description_characters:
                return description
            try:
                frame = await get_video_frame_at_offset(video_path, initial_attempt / 2)
                new_description = await self._generate_image_description(frame)
                if len(new_description) > description:
                    return new_description
            except Exception as e:
                logger.warning(f'failed to generate second-try description for video: {video_path} at offset {initial_attempt / 2}s', exc_info=e)
            return description

        async def _generate_image_description(self, image: Image.Image) -> str:
            vision_lm = await self.model_provider()
            def _generate():
                conversation = [
                    {
                        "role": "User",
                        "content": self.wrapper._get_image_description_prompt(),
                    },
                    {"role": "Assistant", "content": ""},
                ]
                prepare_inputs = vision_lm.chat_processor(
                    conversations=conversation, images=[image], force_batchify=True
                ).to(vision_lm.model.device)
                
                inputs_embeds = vision_lm.model.prepare_inputs_embeds(**prepare_inputs)

                tokenizer = vision_lm.chat_processor.tokenizer
                outputs = vision_lm.model.language_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=prepare_inputs.attention_mask,
                    pad_token_id=tokenizer.eos_token_id,
                    bos_token_id=tokenizer.bos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    max_new_tokens=self.wrapper.max_tokens,
                    do_sample=False,
                    use_cache=True,
                )

                answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
                return answer.strip()
            return await asyncio.get_running_loop().run_in_executor(self.wrapper.executor,  _generate)
