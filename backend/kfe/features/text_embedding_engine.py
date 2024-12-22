import asyncio
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, NamedTuple, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from kfe.utils.model_manager import ModelManager, ModelType


class TextModelWithConfig(NamedTuple):
    model: SentenceTransformer
    query_prefix: str = ''
    passage_prefix: str = ''
    query_encode_kwargs: Optional[dict[str, Any]] = None
    passage_encode_kwargs: Optional[dict[str, Any]] = None

class TextEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager
        self.processing_lock = asyncio.Lock()

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
            model_with_config = await self.model_provider()
            model = model_with_config.model
            prefix = model_with_config.query_prefix if are_queries else model_with_config.passage_prefix
            encode_kwargs = model_with_config.query_encode_kwargs if are_queries else model_with_config.passage_encode_kwargs
            if encode_kwargs is None:
                encode_kwargs = {}

            def _do_generate():
                with torch.no_grad():
                    embeddings = model.encode([x + prefix for x in texts], **encode_kwargs)
                return list(embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True))

            async with self.wrapper.processing_lock:
                return await asyncio.get_running_loop().run_in_executor(None, _do_generate)
