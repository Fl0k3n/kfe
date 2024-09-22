import re
from pathlib import Path
from typing import NamedTuple

import easyocr
from wordfreq import word_frequency

from utils.log import logger


class OCRResult(NamedTuple):
    text: str
    is_screenshot: bool

class OCREngine:
    XD_REGEX = re.compile('x+d+')

    def __init__(self, languages=['pl', 'en'], min_screenshot_words_threshold=5) -> None:
        self.languages = languages
        self.min_screenshot_words_threshold = min_screenshot_words_threshold
        self.model = easyocr.Reader([*languages], gpu=True)

    def run_ocr(self, image_path: Path) -> OCRResult:
        try:
            res = self.model.readtext(str(image_path.absolute()))
        except Exception as e:
            if image_path.suffix != '.gif':
                logger.error(f'Failed to perform OCR on {image_path.name}', exc_info=e)
            return OCRResult(text='', is_screenshot=False)
        full_text = []
        total_words_per_language = [0] * len(self.languages)
        some_language_matched = False

        for (_, text, prob) in res:
            if prob < 0.1:
                continue
            full_text.append(text)
            if not some_language_matched:
                for word in text.split():
                    for i, lang in enumerate(self.languages):
                        if self._is_real_word(lang, word):
                            total_words_per_language[i] += 1
                            if total_words_per_language[i] >= self.min_screenshot_words_threshold:
                                some_language_matched = True
                                break

        return OCRResult(text=' '.join(full_text), is_screenshot=some_language_matched)
    
    def _is_real_word(self, lang: str, word: str) -> bool:
        word = word.lower()
        if self.XD_REGEX.match(word):
            return True
        return word.isalpha() and len(word) > 1 and word_frequency(word, lang, wordlist='small') > 1e-6
