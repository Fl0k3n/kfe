from typing import NamedTuple


class SearchResult(NamedTuple):
    item_idx: int
    score: float # in range [0, 1]
