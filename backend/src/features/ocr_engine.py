import re
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, NamedTuple

import easyocr
from wordfreq import word_frequency

from utils.log import logger
from utils.model_manager import ModelManager, ModelType


class OCRResult(NamedTuple):
    text: str
    is_screenshot: bool

class OCREngine:
    XD_REGEX = re.compile('x+d+')

    def __init__(self, model_manager: ModelManager, languages: list[str], min_screenshot_words_threshold=5) -> None:
        self.languages = languages
        self.min_screenshot_words_threshold = min_screenshot_words_threshold
        self.model_manager = model_manager

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.OCR):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.OCR))

    class Engine:
        def __init__(self, wrapper: "OCREngine", lazy_model_provider: Callable[[], easyocr.Reader]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        def run_ocr(self, image_path: Path) -> OCRResult:
            try:
                res = self.model_provider().readtext(str(image_path.absolute()))
            except Exception as e:
                if image_path.suffix != '.gif':
                    logger.error(f'Failed to perform OCR on {image_path.name}', exc_info=e)
                return OCRResult(text='', is_screenshot=False)
            full_text = []
            total_words_per_language = [0] * len(self.wrapper.languages)
            some_language_matched = False

            for (_, text, prob) in res:
                if prob < 0.1:
                    continue
                full_text.append(text)
                if not some_language_matched:
                    for word in text.split():
                        for i, lang in enumerate(self.wrapper.languages):
                            if self._is_real_word(lang, word):
                                total_words_per_language[i] += 1
                                if total_words_per_language[i] >= self.wrapper.min_screenshot_words_threshold:
                                    some_language_matched = True
                                    break

            return OCRResult(text=' '.join(full_text), is_screenshot=some_language_matched)
        
        def _is_real_word(self, lang: str, word: str) -> bool:
            word = word.lower()
            if self.wrapper.XD_REGEX.match(word):
                return True
            return word.isalpha() and len(word) > 1 and word_frequency(word, lang, wordlist='small') > 1e-6
