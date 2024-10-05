from contextlib import contextmanager
from typing import Callable

import numpy as np
from sentence_transformers import SentenceTransformer

from utils.model_manager import ModelManager, ModelType


class TextEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager, query_prefix: str='', passage_prefix: str='') -> None:
        self.model_manager = model_manager
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.TEXT_EMBEDDING):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TEXT_EMBEDDING))

    class Engine:
        def __init__(self, wrapper: "TextEmbeddingEngine", lazy_model_provider: Callable[[], SentenceTransformer]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        def generate_query_embedding(self, text: str):
            return self.generate_query_embeddings([text])[0]

        def generate_query_embeddings(self, texts: list[str]):
            return self._generate([self.wrapper.query_prefix + x for x in texts])

        def generate_passage_embedding(self, text: str) -> np.ndarray:
            return self.generate_passage_embeddings([text])[0]

        def generate_passage_embeddings(self, texts: list[str]):
            return self._generate([self.wrapper.passage_prefix + x for x in texts])

        def _generate(self, texts: list[str]) -> list[np.ndarray]:
            embeddings = self.model_provider().encode(texts)
            normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            return list(normalized)
        
