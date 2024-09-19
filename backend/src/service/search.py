from typing import Optional

from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata
from search.lexical_search_engine import LexicalSearchEngine
from search.models import AggregatedSearchResult, SearchResult
from search.query_parser import (ParsedSearchQuery, SearchMetric,
                                 SearchQueryParser)
from service.embedding_processor import EmbeddingProcessor


class SearchService:
    def __init__(self, description_lexical_search_engine: LexicalSearchEngine, 
                 embedding_processor: EmbeddingProcessor, file_repo: FileMetadataRepository,
                 parser: SearchQueryParser) -> None:
        self.description_lexical_search_engine = description_lexical_search_engine
        self.embedding_processor = embedding_processor
        self.file_repo = file_repo
        self.parser = parser
        self.lexical_weight = 0.8

    async def search(self, query: str, offset: int, limit: Optional[int]=None) -> tuple[list[AggregatedSearchResult], int]:
        parsed_query = self.parser.parse(query)
        query_text = parsed_query.query_text
        if query_text != '':
            if parsed_query.search_metric == SearchMetric.DESCRIPTION_LEXICAL:
                results = self.description_lexical_search_engine.search(parsed_query.query_text)
            elif parsed_query.search_metric == SearchMetric.DESCRIPTION_SEMANTIC:
                results = self.embedding_processor.search_description_based(parsed_query.query_text, k=100)
            elif parsed_query.search_metric == SearchMetric.OCR_TEXT_SEMANTCIC:
                results = self.embedding_processor.search_ocr_text_based(parsed_query.query_text, k=100)
            else:
                raise
        else:
            results = [SearchResult(item_id=int(x.id), score=1.) for x in await self.file_repo.load_all_files()]

        if not results:
            return [], 0

        file_ids = set(x.item_id for x in results)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(file_ids)
        aggregated_results = []
        for res in results:
            file = files_by_id[res.item_id]
            if not self._filter(parsed_query, file):
                continue
            aggregated_results.append(AggregatedSearchResult(file=file, dense_score=-1., lexical_score=-1., total_score=res.score))

        end = len(aggregated_results) if limit is None else offset + limit
        return aggregated_results[offset:end], len(aggregated_results)
    
    async def search_legacy(self, query: str, offset: int, limit: Optional[int]=None) -> tuple[list[AggregatedSearchResult], int]:
        lexical_results = self.description_lexical_search_engine.search(query)
        dense_results = self.embedding_processor.search_description_based(query, k=100)
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

    async def find_items_with_similar_descriptions(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        search_results = self.embedding_processor.find_items_with_similar_descriptions(file, k=100)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]

    async def find_visually_similar_images(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        search_results = self.embedding_processor.find_visually_similar_images(file, k=100)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]
    
    def _filter(self, parsed_query: ParsedSearchQuery, file: FileMetadata) -> bool:
        if parsed_query.file_type is not None and file.file_type != parsed_query.file_type:
            return False
        if parsed_query.only_screenshot and not file.is_screenshot:
            return False
        return True
