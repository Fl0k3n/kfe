from typing import NamedTuple

from kfe.persistence.model import FileMetadata


class SearchResult(NamedTuple):
    item_id: int
    score: float # in range [0, 1]


class AggregatedSearchResult(NamedTuple):
    file: FileMetadata
    dense_score: float
    lexical_score: float
    total_score: float
