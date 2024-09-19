
import re
from enum import Enum
from typing import NamedTuple, Optional

from persistence.model import FileType
from utils.log import logger


class SearchMetric(Enum):
    DESCRIPTION_LEXICAL = 0 # default
    DESCRIPTION_SEMANTIC = 1 # @sem
    OCR_TEXT_LEXICAL = 2 # @slex
    OCR_TEXT_SEMANTCIC = 3 # @ssem

class ParsedSearchQuery(NamedTuple):
    query_text: str
    search_metric: SearchMetric
    only_screenshot: bool # @ss
    file_type: Optional[FileType] = None # @image @video @audio


class SearchQueryParser:
    QUALIFIERS_RE = re.compile(r'@([\S]+)')

    IMAGE_QUALIFIER = 'image'
    VIDEO_QUALIFIER = 'video'
    AUDIO_QUALIFIER = 'audio'
    SCREENSHOT_QUALIFIER = 'ss'

    DESCRIPTION_SEMANTIC_QUALIFIER = 'sem'
    OCR_TEXT_LEXICAL = 'sslex'
    OCR_TEXT_SEMANTCIC = 'sssem'

    def __init__(self) -> None:
        pass

    def parse(self, raw_query: str) -> ParsedSearchQuery:
        search_metric = SearchMetric.DESCRIPTION_LEXICAL 
        file_type = None
        only_screenshot = False

        for qualifier_match in self.QUALIFIERS_RE.finditer(raw_query):
            qualifier = qualifier_match.group(1)
            if qualifier in (self.IMAGE_QUALIFIER, self.VIDEO_QUALIFIER, self.AUDIO_QUALIFIER):
                file_type = FileType(qualifier)
            elif qualifier == self.SCREENSHOT_QUALIFIER:
                only_screenshot = True
            elif qualifier == self.DESCRIPTION_SEMANTIC_QUALIFIER:
                search_metric = SearchMetric.DESCRIPTION_SEMANTIC 
            elif qualifier == self.OCR_TEXT_LEXICAL:
                search_metric = SearchMetric.OCR_TEXT_LEXICAL
            elif qualifier == self.OCR_TEXT_SEMANTCIC:
                search_metric = SearchMetric.OCR_TEXT_SEMANTCIC
        
        return ParsedSearchQuery(
            query_text=self.QUALIFIERS_RE.sub('', raw_query).strip(),
            file_type=file_type,
            search_metric=search_metric,
            only_screenshot=only_screenshot
        )
