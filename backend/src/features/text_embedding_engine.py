from contextlib import contextmanager
from typing import Callable, NamedTuple

import numpy as np
from sentence_transformers import SentenceTransformer

from utils.model_manager import ModelManager, ModelType


class TextModelWithConfig(NamedTuple):
    model: SentenceTransformer
    query_prefix: str
    passage_prefix: str

class TextEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.TEXT_EMBEDDING):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TEXT_EMBEDDING))

    class Engine:
        def __init__(self, wrapper: "TextEmbeddingEngine", lazy_model_provider: Callable[[], TextModelWithConfig]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        def generate_query_embedding(self, text: str):
            return self.generate_query_embeddings([text])[0]

        def generate_query_embeddings(self, texts: list[str]):
            return self._generate(texts, are_queries=True)

        def generate_passage_embedding(self, text: str) -> np.ndarray:
            return self.generate_passage_embeddings([text])[0]

        def generate_passage_embeddings(self, texts: list[str]):
            return self._generate(texts, are_queries=False)

        def _generate(self, texts: list[str], are_queries: bool) -> list[np.ndarray]:
            model, query_prefix, passage_prefix = self.model_provider()
            prefix = query_prefix if are_queries else passage_prefix
            embeddings = model.encode([x + prefix for x in texts])
            normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            return list(normalized)
        
