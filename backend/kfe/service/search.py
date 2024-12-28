import asyncio
import base64
import io
from typing import NamedTuple, Optional

from PIL import Image

from kfe.features.lemmatizer import Lemmatizer
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata
from kfe.search.lexical_search_engine import LexicalSearchEngine, LexicalTokens
from kfe.search.models import AggregatedSearchResult, SearchResult
from kfe.search.query_parser import (ParsedSearchQuery, SearchMetric,
                                     SearchQueryParser)
from kfe.search.tokenizer import tokenize_text
from kfe.service.embedding_processor import EmbeddingProcessor
from kfe.utils.hybrid_search_confidence_providers import \
    HybridSearchConfidenceProviderFactory
from kfe.utils.search import (combine_results_with_rescoring,
                              confidence_accounting_rrf,
                              reciprocal_rank_fusion)


class HybridSearchConfig(NamedTuple):
    lexical_weight: float = 1.
    semantic_weight: float = 1.
    clip_weight: float = 1.
    rrf_k_constant: int = 60

class SearchService:
    NUM_MAX_SIMILAR_ITEMS_TO_RETURN = 500

    def __init__(self, file_repo: FileMetadataRepository, parser: SearchQueryParser,
                 description_lexical_search_engine: LexicalSearchEngine, 
                 ocr_text_lexical_search_engine: LexicalSearchEngine,
                 transcript_lexical_search_engine: LexicalSearchEngine,
                 embedding_processor: EmbeddingProcessor,
                 lemmatizer: Lemmatizer,
                 hybrid_search_confidence_provider_factory: HybridSearchConfidenceProviderFactory,
                 include_clip_in_hybrid_search: bool,
                 hybrid_search_config: HybridSearchConfig=None) -> None:
        self.file_repo = file_repo
        self.parser = parser
        self.description_lexical_search_engine = description_lexical_search_engine
        self.ocr_text_lexical_search_engine = ocr_text_lexical_search_engine
        self.transcript_lexical_search_engine = transcript_lexical_search_engine
        self.embedding_processor = embedding_processor
        self.lemmatizer = lemmatizer
        self.hybrid_search_confidence_provider_factory = hybrid_search_confidence_provider_factory
        self.include_clip_in_hybrid_search = include_clip_in_hybrid_search
        self.hybrid_search_config = hybrid_search_config if hybrid_search_config is not None else HybridSearchConfig()

    async def search(self, query: str, offset: int, limit: Optional[int]=None) -> tuple[list[AggregatedSearchResult], int]:
        parsed_query = self.parser.parse(query)
        query_text = parsed_query.query_text
        if query_text != '':
            if (named_file := await self.file_repo.get_file_by_name(query_text)) is not None:
                return ([AggregatedSearchResult(named_file, dense_score=0., lexical_score=0., total_score=0.)], 1)
            if parsed_query.search_metric == SearchMetric.HYBRID:
                results = await self.search_hybrid(query_text)
            elif parsed_query.search_metric == SearchMetric.COMBINED_LEXICAL:
                results = self.search_combined_lexical(await self._get_lexical_search_tokens(query_text))
            elif parsed_query.search_metric == SearchMetric.COMBINED_SEMANTIC:
                results = await self.search_combined_semantic(query_text)
            elif parsed_query.search_metric == SearchMetric.DESCRIPTION_LEXICAL:
                results = self.description_lexical_search_engine.search(await self._get_lexical_search_tokens(query_text))
            elif parsed_query.search_metric == SearchMetric.DESCRIPTION_SEMANTIC:
                results = await self.embedding_processor.search_description_based(query_text)
            elif parsed_query.search_metric == SearchMetric.OCR_TEXT_LEXICAL:
                results = self.ocr_text_lexical_search_engine.search(await self._get_lexical_search_tokens(query_text))
            elif parsed_query.search_metric == SearchMetric.OCR_TEXT_SEMANTCIC:
                results = await self.embedding_processor.search_ocr_text_based(query_text)
            elif parsed_query.search_metric == SearchMetric.TRANSCRIPT_LEXICAL:
                results = self.transcript_lexical_search_engine.search(await self._get_lexical_search_tokens(query_text))
            elif parsed_query.search_metric == SearchMetric.TRANSCRIPT_SEMANTCIC:
                results = await self.embedding_processor.search_transcription_text_based(query_text)
            elif parsed_query.search_metric == SearchMetric.CLIP:
                results = await self.search_clip(query_text)
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
            file = files_by_id.get(res.item_id)
            if file is None:
                continue # could be some consistency issue when file was deleted
            if not self._filter(parsed_query, file):
                continue
            aggregated_results.append(AggregatedSearchResult(file=file, dense_score=-1., lexical_score=-1., total_score=res.score))

        end = len(aggregated_results) if limit is None else offset + limit
        return aggregated_results[offset:end], len(aggregated_results)
    
    async def search_hybrid(self, query: str) -> list[SearchResult]:
        lexical_tokens = await self._get_lexical_search_tokens(query)
        lexical_results = self.search_combined_lexical(lexical_tokens)
        semantic_results = await self.search_combined_semantic(query)
        approximate_exact_match_lexical_score = max(
            self.description_lexical_search_engine.get_exact_match_score(lexical_tokens),
            self.ocr_text_lexical_search_engine.get_exact_match_score(lexical_tokens),
            self.transcript_lexical_search_engine.get_exact_match_score(lexical_tokens)
        )
        retriever_results = [lexical_results, semantic_results]
        confidence_providers = [
            self.hybrid_search_confidence_provider_factory.get_lexical_confidence_provider(approximate_exact_match_lexical_score),
            self.hybrid_search_confidence_provider_factory.get_semantic_confidence_provider(),
        ]
        weights = [self.hybrid_search_config.lexical_weight, self.hybrid_search_config.semantic_weight]

        if self.include_clip_in_hybrid_search:
            retriever_results.append(await self.search_clip(query))
            confidence_providers.append(self.hybrid_search_confidence_provider_factory.get_clip_confidence_provider())
            weights.append(self.hybrid_search_config.clip_weight)

        return confidence_accounting_rrf(retriever_results, confidence_providers, weights, self.hybrid_search_config.rrf_k_constant)

    async def search_hybrid_classic(self, query: str) -> list[SearchResult]:
        retriever_results = [
            self.search_combined_lexical(await self._get_lexical_search_tokens(query)),
            await self.search_combined_semantic(query)
        ]
        weights = [self.hybrid_search_config.lexical_weight, self.hybrid_search_config.semantic_weight]
        if self.include_clip_in_hybrid_search:
            retriever_results.append(await self.search_clip(query))
            weights.append(self.hybrid_search_config.clip_weight)
        return reciprocal_rank_fusion(retriever_results, weights, self.hybrid_search_config.rrf_k_constant)
        
    def search_combined_lexical(self, lexical_tokens: LexicalTokens) -> list[SearchResult]:
        return combine_results_with_rescoring(
            all_results=[
                self.description_lexical_search_engine.search(lexical_tokens),
                self.ocr_text_lexical_search_engine.search(lexical_tokens),
                self.transcript_lexical_search_engine.search(lexical_tokens)
            ],
            weights=[0.5, 0.3, 0.2]
        )

    async def search_combined_semantic(self, query: str) -> list[SearchResult]:
        return combine_results_with_rescoring(
            all_results=list(await asyncio.gather(
                self.embedding_processor.search_description_based(query),
                self.embedding_processor.search_ocr_text_based(query),
                self.embedding_processor.search_transcription_text_based(query),
            )),
            weights=[0.5, 0.3, 0.2]
        )

    async def search_clip(self, query: str) -> list[SearchResult]:
        return combine_results_with_rescoring(
            all_results=[
                await self.embedding_processor.search_clip_based(query),
                await self.embedding_processor.search_clip_video_based(query)
            ],
            weights=[0.5, 0.5]
        )
    
    async def find_items_with_similar_descriptions(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        search_results = await self.embedding_processor.find_items_with_similar_descriptions(file, k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]
    
    async def find_items_with_similar_metadata(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        partial_results = []
        if file.description != '':
            srs = await self.embedding_processor.search_text_based_across_all_dimensions(str(file.description), k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
            partial_results.append((srs, 0.5))
        if file.ocr_text is not None and file.ocr_text != '' and file.ocr_text != file.description:
            srs = await self.embedding_processor.search_text_based_across_all_dimensions(str(file.ocr_text), k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
            partial_results.append((srs, 0.25 if len(partial_results) == 1 else 0.5))
        if file.transcript is not None and file.transcript != '' and file.transcript != file.description:
            srs = await self.embedding_processor.search_text_based_across_all_dimensions(str(file.transcript), k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
            partial_results.append((srs, 0.25 if len(partial_results) >= 1 else 0.5))

        if len(partial_results) > 1:
            search_results = combine_results_with_rescoring(*zip(*partial_results))[:self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN]
        elif len(partial_results) == 1:
            search_results = partial_results[0][0]
        else:
            search_results = []
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))

        # assert that input file is returned as first match 
        res = [AggregatedSearchResult(file=file, dense_score=1., lexical_score=1., total_score=1.)]
        for sr in search_results:
            if sr.item_id == int(file.id):
                continue
            res.append(AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score))
        return res

    async def find_visually_similar_images(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        search_results = await self.embedding_processor.find_visually_similar_images(file, k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]
    
    async def find_visually_similar_videos(self, item_id: int) -> list[AggregatedSearchResult]:
        file = await self.file_repo.get_file_by_id(item_id)
        search_results = await self.embedding_processor.find_visually_similar_videos(file, k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
        files_by_id = await self.file_repo.get_files_with_ids_by_id(set(x.item_id for x in search_results))
        return [
            AggregatedSearchResult(file=files_by_id[sr.item_id], dense_score=sr.score, lexical_score=0., total_score=sr.score)
            for sr in search_results
        ]
    
    async def find_visually_similar_images_to_image(self, base64_encoded_image: str) -> list[AggregatedSearchResult]:
        image_data = base64.b64decode(base64_encoded_image)
        buff = io.BytesIO(image_data)
        img = Image.open(buff).convert('RGB')
        search_results = await self.embedding_processor.find_visually_similar_images_to_image(img, k=self.NUM_MAX_SIMILAR_ITEMS_TO_RETURN)
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


    async def _get_lexical_search_tokens(self, query: str) -> LexicalTokens:
        async with self.lemmatizer.run() as engine:
            return LexicalTokens(
                original=tokenize_text(query),
                lemmatized=await engine.lemmatize(query)
            )
