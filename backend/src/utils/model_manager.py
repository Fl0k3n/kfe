from contextlib import contextmanager
from enum import Enum
from threading import Lock
from typing import Any, Callable

from utils.log import logger

Model = Any
ModelProvider = Callable[[], Model]

class ModelType(str, Enum):
    OCR = 'ocr'
    TRANSCRIBER = 'transcriber'
    TEXT_EMBEDDING = 'text-embedding'
    IMAGE_EMBEDDING = 'image-embedding'


class ModelManager:
    def __init__(self, model_providers: dict[ModelType, ModelProvider]) -> None:
        self.model_locks = {m: Lock() for m in ModelType}
        self.model_providers = model_providers
        assert all(model_type in model_providers for model_type in ModelType)
        self.models: dict[ModelType, Model] = {}
        self.model_request_counters: dict[ModelType, int] = {}

    def require_eager(self, model_type: ModelType):
        '''Immediately loads the model if it was not loaded before'''
        self._acquire(model_type)
        self.get_model(model_type)

    def release_eager(self, model_type: ModelType):
        self._release(model_type)

    @contextmanager
    def use(self, model_type: ModelType):
        '''
        Registers model for usage for duration of the context manager.
        Model is not created unless get_model is called, but if it was called
        and there are no more requests the model will be deallocated once contextmanager exits.
        '''
        self._acquire(model_type)
        yield
        self._release(model_type)

    def get_model(self, model_type: ModelType) -> Model:
        '''
        Loads the model if it was not loaded before and returns it.
        The model MUST NOT be kept by the caller after it relased the request.
        '''
        with self.model_locks[model_type]:
            if model_type not in self.models:
                logger.info(f'initializing model: {model_type}')
                self.models[model_type] = self.model_providers[model_type]()
            return self.models[model_type]
        
    def _acquire(self, model_type: ModelType):
        with self.model_locks[model_type]:
            self.model_request_counters[model_type] = self.model_request_counters.get(model_type, 0) + 1
    
    def _release(self, model_type: ModelType):
        with self.model_locks[model_type]:
            count = self.model_request_counters.get(model_type, 0) - 1
            assert count >= 0
            if count == 0 and model_type in self.models:
                logger.info(f'freeing model: {model_type}')
                del self.models[model_type]
