from typing import Optional

from persistence.file_metadata_repository import FileMetadataRepository
from search.lexical_search_engine import LexicalSearchEngine
from search.models import AggregatedSearchResult
from service.embedding_processor import EmbeddingProcessor


class SearchService:
    def __init__(self, description_lexical_search_engine: LexicalSearchEngine, 
                 embedding_processor: EmbeddingProcessor, file_repo: FileMetadataRepository) -> None:
        self.description_lexical_search_engine = description_lexical_search_engine
        self.embedding_processor = embedding_processor
        self.file_repo = file_repo
        self.lexical_weight = 0.8

    async def search(self, query: str, offset: int, limit: Optional[int]=None) -> tuple[list[AggregatedSearchResult], int]:
        lexical_results = self.description_lexical_search_engine.search(query)
        dense_results = self.embedding_processor.search(query, k=100)
        per_id_lexical_results = {x.item_id: x for x in lexical_results}
        per_id_dense_results = {x.item_id: x for x in dense_results}
        all_file_ids = set(per_id_dense_results.keys()).union(per_id_lexical_results.keys())
        files_by_id = await self.file_repo.get_files_with_ids_by_id(all_file_ids)

        aggregated_results: list[AggregatedSearchResult] = []
        for item_id in all_file_ids:
            lexical_score, dense_score = 0., 0.
            if lexical := per_id_lexical_results.get(item_id):
                lexical_score = lexical.score
            if dense := per_id_dense_results.get(item_id):
                dense_score = dense.score
            aggregated_results.append(AggregatedSearchResult(
                file=files_by_id[item_id],
                lexical_score=lexical_score,
                dense_score=dense_score,
                total_score=lexical_score * self.lexical_weight + dense_score * (1 - self.lexical_weight)
            ))

        results = sorted(aggregated_results, key=lambda x: x.total_score, reverse=True)
        end = len(results) if limit is None else offset + limit
        return results[offset:end], len(results)

    async def find_similar_items(self, item_id: int) -> list[AggregatedSearchResult]:
        search_results = self.embedding_processor.find_similar_items(item_id, k=100)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]
