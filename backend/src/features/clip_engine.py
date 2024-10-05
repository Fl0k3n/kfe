

from contextlib import contextmanager
from typing import Callable

import numpy as np
import torch
from PIL.Image import Image
from transformers import CLIPModel, CLIPProcessor

from utils.model_manager import ModelManager, ModelType


class CLIPEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager, device: torch.device):
        self.model_manager = model_manager
        self.device = device

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.CLIP):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.CLIP))

    
    class Engine:
        def __init__(self, wrapper: "CLIPEngine", lazy_model_provider: Callable[[], tuple[CLIPProcessor, CLIPModel]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider    

        def generate_text_embedding(self, text: str) -> np.ndarray:
            processor, model = self.model_provider()
            text_inputs = processor(text=[text], images=None, return_tensors='pt', padding=True).to(self.wrapper.device)
            embedding = model.get_text_features(**text_inputs)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            return embedding.detach().cpu().numpy().ravel()

        def generate_image_embedding(self, img: Image) -> np.ndarray:
            processor, model = self.model_provider()
            img_inputs = processor(text=None, images=img, return_tensors='pt', padding=True).to(self.wrapper.device)
            embedding = model.get_image_features(**img_inputs)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            return embedding.detach().cpu().numpy().ravel()
