import base64
import io
from typing import Optional

import numpy as np
from PIL import Image

from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata
from search.lexical_search_engine import LexicalSearchEngine
from search.models import AggregatedSearchResult, SearchResult
from search.query_parser import (ParsedSearchQuery, SearchMetric,
                                 SearchQueryParser)
from service.embedding_processor import EmbeddingProcessor


class SearchService:
    def __init__(self, file_repo: FileMetadataRepository, parser: SearchQueryParser,
                 description_lexical_search_engine: LexicalSearchEngine, 
                 ocr_text_lexical_search_engine: LexicalSearchEngine,
                 transcript_lexical_search_engine: LexicalSearchEngine,
                 embedding_processor: EmbeddingProcessor) -> None:
        self.description_lexical_search_engine = description_lexical_search_engine
        self.ocr_text_lexical_search_engine = ocr_text_lexical_search_engine
        self.transcript_lexical_search_engine = transcript_lexical_search_engine
        self.embedding_processor = embedding_processor
        self.file_repo = file_repo
        self.parser = parser
        self.lexical_weight = 0.8

    async def search(self, query: str, offset: int, limit: Optional[int]=None) -> tuple[list[AggregatedSearchResult], int]:
        parsed_query = self.parser.parse(query)
        query_text = parsed_query.query_text
        if query_text != '':
            if parsed_query.search_metric == SearchMetric.COMBINED:
                results = self.search_combined(query_text)
            elif parsed_query.search_metric == SearchMetric.COMBINED_LEXICAL:
                results = self.search_combined_lexical(query_text)
            elif parsed_query.search_metric == SearchMetric.COMBINED_SEMANTIC:
                results = self.search_combined_semantic(query_text)
            elif parsed_query.search_metric == SearchMetric.DESCRIPTION_LEXICAL:
                results = self.description_lexical_search_engine.search(query_text)
            elif parsed_query.search_metric == SearchMetric.DESCRIPTION_SEMANTIC:
                results = self.embedding_processor.search_description_based(query_text)
            elif parsed_query.search_metric == SearchMetric.OCR_TEXT_LEXICAL:
                results = self.ocr_text_lexical_search_engine.search(query_text)
            elif parsed_query.search_metric == SearchMetric.OCR_TEXT_SEMANTCIC:
                results = self.embedding_processor.search_ocr_text_based(query_text)
            elif parsed_query.search_metric == SearchMetric.TRANSCRIPT_LEXICAL:
                results = self.transcript_lexical_search_engine.search(query_text)
            elif parsed_query.search_metric == SearchMetric.TRANSCRIPT_SEMANTCIC:
                results = self.embedding_processor.search_transcription_text_based(query_text)
            elif parsed_query.search_metric == SearchMetric.CLIP:
                results = self.embedding_processor.search_clip_based(query_text)
            else:
                raise ValueError('unexpected search metric')
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
    
    def search_combined(self, query: str) -> list[SearchResult]:
        return self.search_combined_lexical(query) # TODO how to unify lexical and semantic scores?

    def search_combined_lexical(self, query: str) -> list[SearchResult]:
        return self._combine_results_with_rescoring(
            all_results=[
                self.description_lexical_search_engine.search(query),
                self.ocr_text_lexical_search_engine.search(query),
                self.transcript_lexical_search_engine.search(query)
            ],
            weights=[0.5, 0.3, 0.2]
        )

    def search_combined_semantic(self, query: str) -> list[SearchResult]:
        return self._combine_results_with_rescoring(
            all_results=[
                self.embedding_processor.search_description_based(query),
                self.embedding_processor.search_ocr_text_based(query),
                self.embedding_processor.search_transcription_text_based(query),
            ],
            weights=[0.5, 0.3, 0.2]
        )
    
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
    
    async def find_visually_similar_images_to_image(self, base64_encoded_image: str) -> list[AggregatedSearchResult]:
        image_data = base64.b64decode(base64_encoded_image)
        buff = io.BytesIO(image_data)
        img = Image.open(buff).convert('RGB')
        search_results = self.embedding_processor.find_visually_similar_images_to_image(img, k=100)
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
        if parsed_query.no_screenshots and file.is_screenshot:
            return False
        return True
    
    def _combine_results_with_rescoring(self, all_results: list[list[SearchResult]], weights: list[float]) -> list[SearchResult]:
        assert len(all_results) == len(weights) and np.isclose(np.sum(weights), 1)
        score_by_id: dict[int, float] = {}
        for dim_results, weight in zip(all_results, weights):
            for sr in dim_results:
                score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + sr.score * weight
        res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
        res.sort(key=lambda x: x.score, reverse=True)
        return res
