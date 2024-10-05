from contextlib import contextmanager
from typing import Callable

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

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.IMAGE_EMBEDDING):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.IMAGE_EMBEDDING))

    class Engine:
        def __init__(self, wrapper: "ImageEmbeddingEngine", lazy_model_provider: Callable[[], tuple[AutoImageProcessor, AutoModel]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        def generate_image_embedding(self, image: Image) -> np.ndarray:
            try:
                processor, model = self.model_provider()
                inputs = processor(image, return_tensors='pt').to(self.wrapper.device)
                embedding: torch.Tensor = model(**inputs).last_hidden_state[:, 0]
                embedding = embedding / torch.linalg.norm(embedding)
                return embedding.detach().cpu().numpy().ravel()
            except Exception as e:
                logger.error('failed to generate image embedding', exc_info=e)
                raise e

        def generate_image_embeddings(self, images: list[Image]) -> list[np.ndarray]:
            return [self.generate_image_embedding(img) for img in images]
