import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

import numpy as np
import torch
from PIL.Image import Image
from transformers import AutoImageProcessor, AutoModel

from utils.log import logger
from utils.model_manager import ModelManager, ModelType


class ImageEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager, device: torch.device):
        self.model_manager = model_manager
        self.device = device

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.IMAGE_EMBEDDING):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.IMAGE_EMBEDDING))

    class Engine:
        def __init__(self, wrapper: "ImageEmbeddingEngine", lazy_model_provider: Callable[[], Awaitable[tuple[AutoImageProcessor, AutoModel]]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def generate_image_embedding(self, image: Image) -> np.ndarray:
            try:
                processor, model = await self.model_provider()
                def _do_generate():
                    inputs = processor(image, return_tensors='pt').to(self.wrapper.device)
                    with torch.no_grad():
                        embedding: torch.Tensor = model(**inputs).last_hidden_state[:, 0]
                    embedding = embedding / torch.linalg.norm(embedding)
                    return embedding.detach().cpu().numpy().ravel()
                return await asyncio.get_running_loop().run_in_executor(None, _do_generate)
            except Exception as e:
                logger.error('failed to generate image embedding', exc_info=e)
                raise e
