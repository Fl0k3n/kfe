import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, Callable, NamedTuple

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
        asyncio.get_running_loop().run_in_executor

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.TEXT_EMBEDDING):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TEXT_EMBEDDING))

    class Engine:
        def __init__(self, wrapper: "TextEmbeddingEngine", lazy_model_provider: Callable[[], Awaitable[TextModelWithConfig]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def generate_query_embedding(self, text: str) -> np.ndarray:
            return (await self.generate_query_embeddings([text]))[0]

        async def generate_query_embeddings(self, texts: list[str]) -> list[np.ndarray]:
            return await self._generate(texts, are_queries=True)

        async def generate_passage_embedding(self, text: str) -> np.ndarray:
            return (await self.generate_passage_embeddings([text]))[0]

        async def generate_passage_embeddings(self, texts: list[str]) -> list[np.ndarray]:
            return await self._generate(texts, are_queries=False)

        async def _generate(self, texts: list[str], are_queries: bool) -> list[np.ndarray]:
            model, query_prefix, passage_prefix = await self.model_provider()
            prefix = query_prefix if are_queries else passage_prefix
            def _do_generate():
                embeddings = model.encode([x + prefix for x in texts])
                return list(embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True))
            return await asyncio.get_running_loop().run_in_executor(None, _do_generate)
