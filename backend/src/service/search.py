from search.lexical_search_engine import LexicalSearchEngine
from search.models import SearchResult
from service.embedding_processor import EmbeddingProcessor


class SearchService:
    def __init__(self, description_lexical_search_engine: LexicalSearchEngine, embedding_processor: EmbeddingProcessor) -> None:
        self.description_lexical_search_engine = description_lexical_search_engine
        self.embedding_processor = embedding_processor

    def search(self, query: str) -> list[SearchResult]:
        return self.description_lexical_search_engine.search(query)

    def search_embedding_based(self, query: str) -> list[SearchResult]:
        res = self.embedding_processor.find_most_similar_items(query)
        return [SearchResult(item_idx=x.item_id, score=(x.similarity + 1) / 2) for x in res]
