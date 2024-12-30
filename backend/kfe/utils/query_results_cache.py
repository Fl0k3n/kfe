from typing import Optional

from kfe.search.models import SearchResult


class QueryResultsCache:
    def __init__(self):
        self.last_query: Optional[str] = None
        self.last_results: Optional[list[SearchResult]] = None

    def put(self, query: str, results: list[SearchResult]):
        self.last_query = query
        self.last_results = results

    def get(self, query: str) -> Optional[list[SearchResult]]:
        return self.last_results if query == self.last_query else None
    
    def invalidate(self):
        self.last_query = self.last_results = None
