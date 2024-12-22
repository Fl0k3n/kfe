import asyncio
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Callable

import torch

from kfe.utils.log import logger

Model = Any
ModelProvider = Callable[[], Model]

class ModelType(str, Enum):
    OCR = 'ocr'
    TRANSCRIBER = 'transcriber'
    TEXT_EMBEDDING = 'text-embedding'
    CLIP = 'clip'
    LEMMATIZER = 'lemmatizer'

class ModelManager:
    MODEL_CLEANUP_DELAY_SECONDS = 60.

    def __init__(self, model_providers: dict[ModelType, ModelProvider]) -> None:
        self.model_locks = {m: asyncio.Lock() for m in ModelType}
        self.model_providers = model_providers
        self.models: dict[ModelType, Model] = {}
        self.model_request_counters: dict[ModelType, int] = {}
        self.model_cleanup_tasks: dict[ModelType, asyncio.Task] = {}

    async def require_eager(self, model_type: ModelType):
        '''Immediately loads the model if it was not loaded before'''
        await self._acquire(model_type)
        await self.get_model(model_type)

    async def release_eager(self, model_type: ModelType):
        await self._release(model_type)

    @asynccontextmanager
    async def use(self, model_type: ModelType):
        '''
        Registers model for usage for duration of the context manager.
        Model is not created unless get_model is called, but if it was called
        and there are no more requests the model will be deallocated once contextmanager exits.
        '''
        await self._acquire(model_type)
        yield
        await self._release(model_type)

    async def get_model(self, model_type: ModelType) -> Model:
        '''
        Loads the model if it was not loaded before and returns it.
        The model MUST NOT be kept by the caller after it relased the request.
        '''
        async with self.model_locks[model_type]:
            if model_type not in self.models:
                logger.info(f'initializing model: {model_type}')
                def _init():
                    return self.model_providers[model_type]()
                self.models[model_type] = await asyncio.get_running_loop().run_in_executor(None, _init)
            return self.models[model_type]
        
    async def _acquire(self, model_type: ModelType):
        async with self.model_locks[model_type]:
            self.model_request_counters[model_type] = self.model_request_counters.get(model_type, 0) + 1
            if (task := self.model_cleanup_tasks.pop(model_type, None)) is not None:
                task.cancel()
    
    async def _release(self, model_type: ModelType):
        async with self.model_locks[model_type]:
            count = self.model_request_counters.get(model_type, 0) - 1
            self.model_request_counters[model_type] = count
            assert count >= 0
            if count == 0 and model_type in self.models:
                if (task := self.model_cleanup_tasks.get(model_type)) is not None:
                    task.cancel()
                self.model_cleanup_tasks[model_type] = asyncio.create_task(self._del_model_after_delay_if_not_reacquired(model_type))

    async def _del_model_after_delay_if_not_reacquired(self, model_type: ModelType):
        await asyncio.sleep(self.MODEL_CLEANUP_DELAY_SECONDS)
        async with self.model_locks[model_type]:
            if self.model_request_counters.get(model_type, 0) == 0 and model_type in self.models:
                logger.info(f'freeing model: {model_type}')
                del self.models[model_type]
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

class SecondaryModelManager(ModelManager):
    def __init__(self, primary: ModelManager, owned_model_providers: dict[ModelType, ModelProvider]):
        super().__init__(owned_model_providers)
        self.primary = primary
        self.owned_model_providers = owned_model_providers

    async def _acquire(self, model_type: ModelType):
        if model_type in self.owned_model_providers:
            await super()._acquire(model_type)
        else:
            await self.primary._acquire(model_type)
    
    async def _release(self, model_type: ModelType):
        if model_type in self.owned_model_providers:
            await super()._release(model_type)
        else:
            await self.primary._release(model_type)

    async def get_model(self, model_type: ModelType) -> Model:
        if model_type in self.owned_model_providers:
            return await super().get_model(model_type)
        else:
            return await self.primary.get_model(model_type)
