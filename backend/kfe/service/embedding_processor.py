from pathlib import Path
from typing import Awaitable, Callable, NamedTuple, Optional

import numpy as np
from PIL import Image
from tqdm import tqdm

from kfe.features.clip_engine import CLIPEngine
from kfe.features.text_embedding_engine import TextEmbeddingEngine
from kfe.persistence.embeddings import (EmbeddingPersistor,
                                        MutableTextEmbedding, StoredEmbeddings,
                                        StoredEmbeddingType)
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata, FileType
from kfe.search.embedding_similarity_calculator import \
    EmbeddingSimilarityCalculator
from kfe.search.models import SearchResult
from kfe.search.multi_embedding_similarity_calculator import \
    MultiEmbeddingSimilarityCalculator
from kfe.utils.init_progress_tracker import InitProgressTracker, InitState
from kfe.utils.log import logger
from kfe.utils.search import combine_results_with_rescoring
from kfe.utils.video_frames_extractor import (get_video_duration_seconds,
                                              get_video_frame_at_offset)


class ClipVideoFrameSelectionConfig(NamedTuple):
    max_frames: int = 10
    min_seconds_between_frame: float = 3.

class EmbeddingProcessor:
    def __init__(self, root_dir: Path,
                 persistor: EmbeddingPersistor,
                 text_embedding_engine: TextEmbeddingEngine,
                 clip_engine: CLIPEngine, clip_video_cfg: ClipVideoFrameSelectionConfig=None) -> None:
        self.root_dir = root_dir
        self.persistor = persistor
        self.text_embedding_engine = text_embedding_engine
        self.clip_engine = clip_engine
        self.clip_video_cfg = clip_video_cfg if clip_video_cfg is not None else ClipVideoFrameSelectionConfig()
            
        self.description_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.ocr_text_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.transcription_text_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.clip_image_similarity_calculator: EmbeddingSimilarityCalculator = None
        self.clip_video_similarity_calculator: MultiEmbeddingSimilarityCalculator = None

    async def init_embeddings(self, file_repo: FileMetadataRepository, progress_tracker: InitProgressTracker):
        all_files = await file_repo.load_all_files()
        files_by_name = {str(x.name): x for x in all_files}
        description_builder = EmbeddingSimilarityCalculator.Builder()
        ocr_text_builder = EmbeddingSimilarityCalculator.Builder()
        transcription_text_builder = EmbeddingSimilarityCalculator.Builder()
        clip_image_builder = EmbeddingSimilarityCalculator.Builder()
        clip_video_builder = MultiEmbeddingSimilarityCalculator.Builder()

        progress_tracker.enter_state(InitState.EMBEDDING, len(all_files))

        # reconcile files which have some (possibly outdated) embeddings
        for file_name in tqdm(self.persistor.get_all_embedded_files(), desc='initializing embeddings'):
            file = files_by_name.pop(file_name, None)
            try:
                if file is None:
                    self.persistor.delete(file_name)
                else:
                    dirty = False
                    try:
                        embeddings = self.persistor.load(file_name, expected_texts={
                            StoredEmbeddingType.DESCRIPTION: str(file.description),
                            StoredEmbeddingType.OCR_TEXT: str(file.ocr_text) if file.is_screenshot else '',
                            StoredEmbeddingType.TRANSCRIPTION_TEXT: str(file.transcript) if file.is_transcript_analyzed else ''
                        })
                    except Exception:
                        embeddings = StoredEmbeddings()
                    if file.description == '':
                        if embeddings.description is not None:
                            embeddings = embeddings.without(StoredEmbeddingType.DESCRIPTION)
                            dirty = True
                    elif embeddings.description is None:
                        await self._create_text_embedding(file.description, embeddings, StoredEmbeddingType.DESCRIPTION)
                        dirty = True
                    if file.file_type == FileType.IMAGE and embeddings.clip_image is None and not file.embedding_generation_failed:
                        await self._create_clip_image_embedding(file, embeddings)
                        dirty = True
                    if file.file_type == FileType.VIDEO and embeddings.clip_video is None and not file.embedding_generation_failed:
                        if await self._create_clip_video_embeddings(file, embeddings) is not None:
                            dirty = True
                    if file.is_screenshot and file.is_ocr_analyzed and file.ocr_text != '' and embeddings.ocr_text is None:
                        await self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
                        dirty = True
                    if file.is_transcript_analyzed and file.transcript and file.transcript != '' is not None and embeddings.transcription_text is None:
                        await self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
                        dirty = True

                    if embeddings.description is not None:
                        description_builder.add_row(file.id, embeddings.description.embedding)
                    if embeddings.clip_image is not None:
                        clip_image_builder.add_row(file.id, embeddings.clip_image)
                    if embeddings.ocr_text is not None:
                        ocr_text_builder.add_row(file.id, embeddings.ocr_text.embedding)
                    if embeddings.transcription_text is not None:
                        transcription_text_builder.add_row(file.id, embeddings.transcription_text.embedding)
                    if embeddings.clip_video is not None:
                        clip_video_builder.add_rows(file.id, embeddings.clip_video)

                    if dirty:
                        self.persistor.save(file.name, embeddings)
            except Exception as e:
                logger.error(f'failed to init embeddings for {file.name}', exc_info=e)
            progress_tracker.mark_file_processed()

        # reconcile new files that didn't have any embeddings before
        for file in tqdm(files_by_name.values(), desc='initializing embeddings'):
            embeddings = StoredEmbeddings()
            try:
                if file.description != '':
                    await self._create_text_embedding(file.description, embeddings, StoredEmbeddingType.DESCRIPTION)
                    description_builder.add_row(file.id, embeddings.description.embedding)
                if file.file_type == FileType.IMAGE and not file.embedding_generation_failed:
                    if await self._create_clip_image_embedding(file, embeddings) is not None: 
                        clip_image_builder.add_row(file.id, embeddings.clip_image)
                if file.file_type == FileType.VIDEO and not file.embedding_generation_failed:
                    if await self._create_clip_video_embeddings(file, embeddings) is not None:
                        clip_video_builder.add_rows(file.id, embeddings.clip_video)
                if file.is_screenshot and file.is_ocr_analyzed and file.ocr_text != '':
                    await self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
                    ocr_text_builder.add_row(file.id, embeddings.ocr_text.embedding)
                if file.is_transcript_analyzed and file.transcript is not None and file.transcript != '':
                    await self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
                    transcription_text_builder.add_row(file.id, embeddings.transcription_text.embedding)
                self.persistor.save(file.name, embeddings)
            except Exception as e:
                logger.error(f'failed to init embeddings for {file.name}', exc_info=e)
            progress_tracker.mark_file_processed()

        self.description_similarity_calculator = description_builder.build()
        self.ocr_text_similarity_calculator = ocr_text_builder.build()
        self.transcription_text_similarity_calculator= transcription_text_builder.build()
        self.clip_image_similarity_calculator = clip_image_builder.build()
        self.clip_video_similarity_calculator = clip_video_builder.build()

    async def search_description_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        async with self.text_embedding_engine.run() as engine:
            query_embedding = await engine.generate_query_embedding(query)
        return self.description_similarity_calculator.compute_similarity(query_embedding, k)
    
    async def search_ocr_text_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        async with self.text_embedding_engine.run() as engine:
            query_embedding = await engine.generate_query_embedding(query)
        return self.ocr_text_similarity_calculator.compute_similarity(query_embedding, k)
    
    async def search_transcription_text_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        async with self.text_embedding_engine.run() as engine:
            query_embedding = await engine.generate_query_embedding(query)
        return self.transcription_text_similarity_calculator.compute_similarity(query_embedding, k)
    
    async def search_text_based_across_all_dimensions(self, query: str, k: Optional[int]=None, d_o_t_weights: Optional[tuple[float, float, float]]=None) -> list[SearchResult]:
        if d_o_t_weights is None:
            d_o_t_weights = (0.5, 0.3, 0.2)
        async with self.text_embedding_engine.run() as engine:
            query_embedding = await engine.generate_query_embedding(query)
        d, o, t = [], [], []
        if d_o_t_weights[0] != 0:
            d = self.description_similarity_calculator.compute_similarity(query_embedding, k)
        if d_o_t_weights[1] != 0:
            o = self.ocr_text_similarity_calculator.compute_similarity(query_embedding, k)
        if d_o_t_weights[2] != 0:
            t = self.transcription_text_similarity_calculator.compute_similarity(query_embedding, k)
        return combine_results_with_rescoring([d, o, t], list(d_o_t_weights))
    
    async def search_clip_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        async with self.clip_engine.run() as engine:
            query_embedding = await engine.generate_text_embedding(query)
        return self.clip_image_similarity_calculator.compute_similarity(query_embedding, k)
    
    async def search_clip_video_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        async with self.clip_engine.run() as engine:
            query_embedding = await engine.generate_text_embedding(query)
        return self.clip_video_similarity_calculator.compute_similarity(query_embedding, k)
    
    async def find_items_with_similar_descriptions(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.description == '':
            return [SearchResult(item_id=file.id, score=1.)]
        return await self._find_similar_items(file, k, self.description_similarity_calculator,
             lambda: self._create_description_embedding(file, StoredEmbeddings()))
    
    async def find_items_with_similar_transcript(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.transcript == '':
            return [SearchResult(item_id=file.id, score=1.)]
        return await self._find_similar_items(file, k, self.transcription_text_similarity_calculator,
             lambda: self._create_transcription_text_embedding(file, StoredEmbeddings()))

    async def find_items_with_similar_ocr_text(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.transcript == '':
            return [SearchResult(item_id=file.id, score=1.)]
        return await self._find_similar_items(file, k, self.ocr_text_similarity_calculator,
             lambda: self._create_text_embedding(file.ocr_text, StoredEmbeddings(), StoredEmbeddingType.OCR_TEXT))
    
    async def find_visually_similar_images(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.file_type != FileType.IMAGE:
            return [SearchResult(item_id=file.id, score=1.)]
        return await self._find_similar_items(file, k, self.clip_image_similarity_calculator,
             lambda: self._create_clip_image_embedding(file, StoredEmbeddings()))
    
    async def find_visually_similar_videos(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.file_type != FileType.IMAGE:
            return [SearchResult(item_id=file.id, score=1.)]
        emb = self.clip_image_similarity_calculator.get_embedding(file.id)
        if emb is None:
            emb = await self._create_clip_image_embedding(file, StoredEmbeddings())
        return self.clip_video_similarity_calculator.compute_similarity(emb, k)
    
    async def find_visually_similar_images_to_image(self, img: Image, k: int=100) -> list[SearchResult]:
        return self.clip_image_similarity_calculator.compute_similarity(await self._embed_image_clip(img), k)
    
    async def update_description_embedding(self, file: FileMetadata, old_description: str):
        await self._update_text_embedding(file, old_description, file.description, self.description_similarity_calculator, StoredEmbeddingType.DESCRIPTION)

    async def update_transcript_embedding(self, file: FileMetadata, old_transcript: str):
        await self._update_text_embedding(file, old_transcript, file.transcript, self.transcription_text_similarity_calculator, StoredEmbeddingType.TRANSCRIPTION_TEXT)

    async def update_ocr_text_embedding(self, file: FileMetadata, old_ocr_text: str):
        await self._update_text_embedding(file, old_ocr_text, file.ocr_text, self.ocr_text_similarity_calculator, StoredEmbeddingType.OCR_TEXT)

    async def on_file_created(self, file: FileMetadata):
        embeddings = StoredEmbeddings()
        if file.description != '':
            self.description_similarity_calculator.add(file.id, await self._create_description_embedding(file, embeddings))
        if file.file_type == FileType.IMAGE:
            if await self._create_clip_image_embedding(file, embeddings) is not None:
                self.clip_image_similarity_calculator.add(file.id, embeddings.clip_image)
        if file.file_type == FileType.VIDEO:
            if await self._create_clip_video_embeddings(file, embeddings) is not None:
                self.clip_video_similarity_calculator.add(file.id, embeddings.clip_video)
        if file.is_screenshot and file.is_ocr_analyzed and file.ocr_text != '':
            await self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
            self.ocr_text_similarity_calculator.add(file.id, embeddings.ocr_text.embedding)
        if file.is_transcript_analyzed and file.transcript is not None and file.transcript != '':
            await self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
            self.transcription_text_similarity_calculator.add(file.id, embeddings.transcription_text.embedding)
        self.persistor.save(file.name, embeddings)

    async def on_file_deleted(self, file: FileMetadata):
        self.persistor.delete(file.name)
        if file.file_type == FileType.IMAGE:
            self.clip_image_similarity_calculator.delete(file.id)
        if file.file_type == FileType.VIDEO:
            self.clip_video_similarity_calculator.delete(file.id)
        if file.is_ocr_analyzed:
            self.ocr_text_similarity_calculator.delete(file.id)
        if file.is_transcript_analyzed:
            self.transcription_text_similarity_calculator.delete(file.id)
        self.description_similarity_calculator.delete(file.id)

    async def _update_text_embedding(self, file: FileMetadata, old_text: str, new_text: str, calc: EmbeddingSimilarityCalculator, embedding_type: StoredEmbeddingType):
        embeddings = self.persistor.load_without_consistency_check(file.name)
        fid = int(file.id)
        if new_text != '':    
            embedding = await self._create_text_embedding(new_text, embeddings, embedding_type)
            self.persistor.save(file.name, embeddings)
            if old_text == '':
                calc.add(fid, embedding)
            else:
                calc.replace(fid, embedding)
        else:
            calc.delete(fid)
            self.persistor.save(file.name, embeddings.without(embedding_type))
        
    async def _find_similar_items(self,
        file: FileMetadata,
        k: int,
        calculator: EmbeddingSimilarityCalculator,
        embedding_provider: Callable[[], Awaitable[np.ndarray]]
    ) -> list[SearchResult]:
        this = SearchResult(item_id=file.id, score=1.)
        emb = calculator.get_embedding(file.id)
        add_this = False
        if emb is None:
            emb = await embedding_provider()
            add_this = True
        res = calculator.compute_similarity(emb, k)
        if add_this:
            res = [this, *res]
        return res
    
    async def _create_text_embedding(self, text: str, embeddings: StoredEmbeddings, embedding_type: StoredEmbeddingType) -> np.ndarray:
        res = await self._create_mutable_text_embedding(text)
        embeddings[embedding_type] = res
        return res.embedding

    async def _create_description_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray: 
        embeddings.description = await self._create_mutable_text_embedding(file.description)
        return embeddings.description.embedding
    
    async def _create_transcription_text_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        embeddings.transcription_text = await self._create_mutable_text_embedding(file.transcript)
        return embeddings.transcription_text.embedding
    
    async def _create_mutable_text_embedding(self, text: str) -> MutableTextEmbedding:
        async with self.text_embedding_engine.run() as engine:
            return MutableTextEmbedding(text=text, embedding=await engine.generate_passage_embedding(text))
    
    async def _create_clip_image_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> Optional[np.ndarray]:
        try:
            img = Image.open(self.root_dir.joinpath(file.name)).convert('RGB')
            embeddings.clip_image = await self._embed_image_clip(img)
            return embeddings.clip_image
        except Exception as e:
            logger.error(f'failed to generate clip image embedding for file: {file.name}', exc_info=e)
            file.embedding_generation_failed = True
            return None
    
    async def _create_clip_video_embeddings(self, file: FileMetadata, embeddings: StoredEmbeddings) -> Optional[np.ndarray]: 
        try:
            video_duration = await get_video_duration_seconds(self.root_dir.joinpath(file.name))
            async with self.clip_engine.run() as engine:
                frame_embeddings = []
                num_video_frames = min(self.clip_video_cfg.max_frames, max(int(video_duration / self.clip_video_cfg.min_seconds_between_frame), 1))
                for i in range(num_video_frames):
                    # TODO smarter frame selection
                    offset = video_duration * ((2 * i + 1) / (2 * num_video_frames))
                    img = await get_video_frame_at_offset(self.root_dir.joinpath(file.name), offset)
                    frame_embeddings.append(await engine.generate_image_embedding(img))
                embeddings.clip_video = np.vstack(frame_embeddings)
            return embeddings.clip_video
        except Exception as e:
            logger.error(f'failed to generate clip video embeddings for file: {file.name}', exc_info=e)
            file.embedding_generation_failed = True
            return None

    async def _embed_image_clip(self, image: Image.Image) -> np.ndarray:
        async with self.clip_engine.run() as engine:
            return await engine.generate_image_embedding(image)
