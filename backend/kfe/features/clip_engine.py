

import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

import numpy as np
import torch
from PIL.Image import Image
from transformers import CLIPModel, CLIPProcessor

from kfe.utils.model_manager import ModelManager, ModelType


class CLIPEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager, device: torch.device):
        self.model_manager = model_manager
        self.device = device
        self.processing_lock = asyncio.Lock()

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.CLIP):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.CLIP))

    class Engine:
        def __init__(self, wrapper: "CLIPEngine", lazy_model_provider: Callable[[], Awaitable[tuple[CLIPProcessor, CLIPModel]]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider    

        async def generate_text_embedding(self, text: str) -> np.ndarray:
            processor, model = await self.model_provider()
            def _do_generate():
                text_inputs = processor(text=[text], images=None, return_tensors='pt', padding=True).to(self.wrapper.device)
                with torch.no_grad():
                    embedding = model.get_text_features(**text_inputs).float()
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                return embedding.detach().cpu().numpy().ravel()
            async with self.wrapper.processing_lock:
                return await asyncio.get_running_loop().run_in_executor(None, _do_generate)

        async def generate_image_embedding(self, img: Image) -> np.ndarray:
            processor, model = await self.model_provider()
            def _do_generate():
                img_inputs = processor(text=None, images=img, return_tensors='pt', padding=True).to(self.wrapper.device)
                with torch.no_grad():
                    embedding = model.get_image_features(**img_inputs).float()
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                return embedding.detach().cpu().numpy().ravel()
            async with self.wrapper.processing_lock:
                return await asyncio.get_running_loop().run_in_executor(None, _do_generate)
