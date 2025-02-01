import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Awaitable, Callable, NamedTuple

from kfe.features.visionlmutils.janus.modeling_vlm import MultiModalityCausalLM
from kfe.features.visionlmutils.janus.processing_vlm import VLChatProcessor
from kfe.features.visionlmutils.janus.utils.io import load_pil_images
from kfe.utils.model_manager import ModelManager, ModelType


class VisionLMModel(NamedTuple):
    model: MultiModalityCausalLM
    chat_processor: VLChatProcessor

class VisionLMEngine:
    def __init__(self, model_manager: ModelManager, max_tokens=200):
        self.model_manager = model_manager
        self.max_tokens = max_tokens
        self.processing_lock = asyncio.Lock()

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

        async def generate_description(self, image_path: Path) -> str:
            async with self.wrapper.processing_lock:
                vision_lm = await self.model_provider()
                def _generate():
                    conversation = [
                        {
                            "role": "User",
                            "content": self.wrapper._get_image_description_prompt(),
                            "images": [str(image_path.absolute())],
                        },
                        {"role": "Assistant", "content": ""},
                    ]
                    pil_images = load_pil_images(conversation)
                    prepare_inputs = vision_lm.chat_processor(
                        conversations=conversation, images=pil_images, force_batchify=True
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
                    return answer
                return await asyncio.get_running_loop().run_in_executor(None,  _generate)
