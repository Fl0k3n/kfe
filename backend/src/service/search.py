from search.lexical_search_engine import LexicalSearchEngine
from search.models import SearchResult


class SearchService:
    def __init__(self, description_lexical_search_engine: LexicalSearchEngine) -> None:
        self.description_lexical_search_engine = description_lexical_search_engine

    def search(self, query: str) -> list[SearchResult]:
        return self.description_lexical_search_engine.search(query)
