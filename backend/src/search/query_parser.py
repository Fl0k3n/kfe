
import re
from enum import Enum
from typing import NamedTuple, Optional

from persistence.model import FileType
from utils.log import logger


class SearchMetric(Enum):
    COMBINED            = 0 # default
    COMBINED_LEXICAL    = 1 # @lex
    COMBINED_SEMANTIC   = 2 # @sem

    DESCRIPTION_LEXICAL  = 3 # @dlex
    DESCRIPTION_SEMANTIC = 4 # @dsem

    OCR_TEXT_LEXICAL   = 5 # @olex
    OCR_TEXT_SEMANTCIC = 6 # @osem

    TRANSCRIPT_LEXICAL   = 7 # @tlex
    TRANSCRIPT_SEMANTCIC = 8 # @tsem

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

    def __init__(self) -> None:
        self.search_metric_qualifiers = {
            'lex': SearchMetric.COMBINED_LEXICAL,
            'sem': SearchMetric.COMBINED_SEMANTIC,
            'dlex': SearchMetric.DESCRIPTION_LEXICAL,
            'dsem': SearchMetric.DESCRIPTION_SEMANTIC,
            'olex': SearchMetric.OCR_TEXT_LEXICAL,
            'osem': SearchMetric.OCR_TEXT_SEMANTCIC,
            'tlex': SearchMetric.TRANSCRIPT_LEXICAL,
            'tsem': SearchMetric.TRANSCRIPT_SEMANTCIC,
        }

    def parse(self, raw_query: str) -> ParsedSearchQuery:
        search_metric = SearchMetric.COMBINED 
        file_type = None
        only_screenshot = False

        for qualifier_match in self.QUALIFIERS_RE.finditer(raw_query):
            qualifier = qualifier_match.group(1)
            if qualifier in (self.IMAGE_QUALIFIER, self.VIDEO_QUALIFIER, self.AUDIO_QUALIFIER):
                file_type = FileType(qualifier)
            elif qualifier == self.SCREENSHOT_QUALIFIER:
                only_screenshot = True
            elif metric := self.search_metric_qualifiers.get(qualifier):
                search_metric = metric
        
        return ParsedSearchQuery(
            query_text=self.QUALIFIERS_RE.sub('', raw_query).strip(),
            file_type=file_type,
            search_metric=search_metric,
            only_screenshot=only_screenshot
        )
