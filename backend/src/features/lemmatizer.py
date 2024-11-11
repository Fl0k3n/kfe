import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

import spacy

from utils.model_manager import ModelManager, ModelType


class Lemmatizer:
    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.LEMMATIZER):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.LEMMATIZER))

    class Engine:
        def __init__(self, wrapper: "Lemmatizer", lazy_model_provider: Callable[[], Awaitable[spacy.language.Language]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def lemmatize(self, text: str) -> list[str]:
            model = await self.model_provider()
            def _do_lemmatize():
                lemmatized = model(text)
                res = []
                for token_group in lemmatized:
                    res.extend(token_group.lemma_.split())
                return [x.lower() for x in res]
            return await asyncio.get_running_loop().run_in_executor(None, _do_lemmatize)
