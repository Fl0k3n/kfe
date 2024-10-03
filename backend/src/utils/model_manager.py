from contextlib import contextmanager
from enum import Enum
from typing import Any

import easyocr
from huggingsound import SpeechRecognitionModel


class ModelType(str, Enum):
    OCR = 'ocr'
    TRANSCRIBER = 'transcriber'


# NOT thread safe
class ModelManager:
    def __init__(self, ocr_languages: list[str]) -> None:
        self.ocr_languages = ocr_languages
        self.models = {}
        self.model_request_counters = {}

    @contextmanager
    def use(self, model_type: ModelType):
        '''
        Registers model for usage for duration of the context manager.
        Model is not created unless get_model is called, but if it was called
        and there are no more requests the model will be deallocated once contextmanager exits.
        '''
        count = self.model_request_counters.get(model_type, 0)
        self.model_request_counters[model_type] = count + 1
        yield
        count = self.model_request_counters.get(model_type, 0) - 1
        assert count >= 0
        if count == 0 and model_type in self.models:
            del self.models[model_type]

    def get_model(self, model_type: ModelType) -> Any:
        if model_type not in self.models:
            if model_type == ModelType.OCR:
                self.models[model_type] = easyocr.Reader([*self.ocr_languages], gpu=True)
            elif model_type == ModelType.TRANSCRIBER:
                self.models[model_type] = SpeechRecognitionModel("jonatasgrosman/wav2vec2-large-xlsr-53-polish")
            else:
                raise KeyError(f'unknown model type: {model_type}')
        return self.models[model_type]
    
