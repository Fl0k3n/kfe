from pathlib import Path
from typing import Callable, Optional

import numpy as np
from PIL import Image

from features.clip_engine import CLIPEngine
from features.image_embedding_engine import ImageEmbeddingEngine
from features.text_embedding_engine import TextEmbeddingEngine
from persistence.embeddings import (EmbeddingPersistor, MutableTextEmbedding,
                                    StoredEmbeddings, StoredEmbeddingType)
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata, FileType
from search.embedding_similarity_calculator import \
    EmbeddingSimilarityCalculator
from search.models import SearchResult
from search.multi_embedding_similarity_calculator import \
    MultiEmbeddingSimilarityCalculator
from utils.log import logger
from utils.video_frames_extractor import (get_video_duration_seconds,
                                          get_video_frame_at_offset)


class EmbeddingProcessor:
    def __init__(self, root_dir: Path, file_repo: FileMetadataRepository,
                 persistor: EmbeddingPersistor,
                 text_embedding_engine: TextEmbeddingEngine,
                 image_embedding_engine: ImageEmbeddingEngine,
                 clip_engine: CLIPEngine, num_clip_video_frames=3) -> None:
        self.root_dir = root_dir
        self.file_repo = file_repo
        self.persistor = persistor
        self.text_embedding_engine = text_embedding_engine
        self.image_embedding_engine = image_embedding_engine
        self.clip_engine = clip_engine
        self.num_clip_video_frames = num_clip_video_frames
        assert self.num_clip_video_frames >= 1
            
        self.description_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.image_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.ocr_text_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.transcription_text_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.clip_image_similarity_calculator: EmbeddingSimilarityCalculator = None
        self.clip_video_similarity_calculator: MultiEmbeddingSimilarityCalculator = None

    async def init_embeddings(self):
        all_files = await self.file_repo.load_all_files()
        files_by_name = {str(x.name): x for x in all_files}
        description_builder = EmbeddingSimilarityCalculator.Builder()
        image_builder = EmbeddingSimilarityCalculator.Builder()
        ocr_text_builder = EmbeddingSimilarityCalculator.Builder()
        transcription_text_builder = EmbeddingSimilarityCalculator.Builder()
        clip_image_builder = EmbeddingSimilarityCalculator.Builder()
        clip_video_builder = MultiEmbeddingSimilarityCalculator.Builder()
         
        for file_name in self.persistor.get_all_embedded_files():
            file = files_by_name.pop(file_name, None)
            if file is None:
                self.persistor.delete(file_name)
            else:
                dirty = False
                embeddings = self.persistor.load(file_name, expected_texts={
                    StoredEmbeddingType.DESCRIPTION: str(file.description),
                    StoredEmbeddingType.OCR_TEXT: str(file.ocr_text) if file.is_screenshot else '',
                    StoredEmbeddingType.TRANSCRIPTION_TEXT: str(file.transcript) if file.is_transcript_analyzed else ''
                })
                if file.description == '':
                    if embeddings.description is not None:
                        embeddings = embeddings.without(StoredEmbeddingType.DESCRIPTION)
                        dirty = True
                elif embeddings.description is None:
                    self._create_text_embedding(file.description, embeddings, StoredEmbeddingType.DESCRIPTION)
                    dirty = True
                if file.file_type == FileType.IMAGE and embeddings.image is None:
                    self._create_image_embedding(file, embeddings)
                    dirty = True
                if file.file_type == FileType.IMAGE and embeddings.clip_image is None:
                    self._create_clip_image_embedding(file, embeddings)
                    dirty = True
                if file.file_type == FileType.VIDEO and embeddings.clip_video is None and not file.has_video_embedding_failed:
                    if await self._create_clip_video_embeddings(file, embeddings) is not None:
                        dirty = True
                if file.is_screenshot and file.is_ocr_analyzed and embeddings.ocr_text is None:
                    self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
                    dirty = True
                if file.is_transcript_analyzed and file.transcript is not None and embeddings.transcription_text is None:
                    self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
                    dirty = True

                if embeddings.description is not None:
                    description_builder.add_row(file.id, embeddings.description.embedding)
                if embeddings.image is not None:
                    image_builder.add_row(file.id, embeddings.image)
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

        for file in files_by_name.values():
            embeddings = StoredEmbeddings()
            if file.description != '':
                self._create_text_embedding(file.description, embeddings, StoredEmbeddingType.DESCRIPTION)
                description_builder.add_row(file.id, embeddings.description.embedding)
            if file.file_type == FileType.IMAGE:
                image_builder.add_row(file.id, self._create_image_embedding(file, embeddings))
                clip_image_builder.add_row(file.id, self._create_clip_image_embedding(file, embeddings))
            if file.file_type == FileType.VIDEO:
                if await self._create_clip_video_embeddings(file, embeddings) is not None:
                    clip_video_builder.add_rows(file.id, embeddings.clip_video)
            if file.is_screenshot and file.is_ocr_analyzed:
                self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
                ocr_text_builder.add_row(file.id, embeddings.ocr_text.embedding)
            if file.is_transcript_analyzed and file.transcript is not None:
                self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
                transcription_text_builder.add_row(file.id, embeddings.transcription_text.embedding)
            self.persistor.save(file.name, embeddings)

        self.description_similarity_calculator = description_builder.build()
        self.image_similarity_calculator = image_builder.build()
        self.ocr_text_similarity_calculator = ocr_text_builder.build()
        self.transcription_text_similarity_calculator= transcription_text_builder.build()
        self.clip_image_similarity_calculator = clip_image_builder.build()
        self.clip_video_similarity_calculator = clip_video_builder.build()

    def search_description_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        with self.text_embedding_engine.run() as engine:
            query_embedding = engine.generate_query_embedding(query)
        return self.description_similarity_calculator.compute_similarity(query_embedding, k)
    
    def search_ocr_text_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        with self.text_embedding_engine.run() as engine:
            query_embedding = engine.generate_query_embedding(query)
        return self.ocr_text_similarity_calculator.compute_similarity(query_embedding, k)
    
    def search_transcription_text_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        with self.text_embedding_engine.run() as engine:
            query_embedding = engine.generate_query_embedding(query)
        return self.transcription_text_similarity_calculator.compute_similarity(query_embedding, k)
    
    def search_clip_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        with self.clip_engine.run() as engine:
            query_embedding = engine.generate_text_embedding(query)
        return self.clip_image_similarity_calculator.compute_similarity(query_embedding, k)
    
    def search_clip_video_based(self, query: str, k: Optional[int]=None) -> list[SearchResult]:
        with self.clip_engine.run() as engine:
            query_embedding = engine.generate_text_embedding(query)
        return self.clip_video_similarity_calculator.compute_similarity(query_embedding, k)
    
    def find_items_with_similar_descriptions(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.description == '':
            return SearchResult(item_id=file.id, score=1.)
        return self._find_similar_items(file, k, self.description_similarity_calculator,
             lambda: self._create_description_embedding(file, StoredEmbeddings()))
    
    def find_visually_similar_images(self, file: FileMetadata, k: int=100) -> list[SearchResult]:
        if file.file_type != FileType.IMAGE:
            return SearchResult(item_id=file.id, score=1.)
        return self._find_similar_items(file, k, self.image_similarity_calculator,
             lambda: self._create_image_embedding(file, StoredEmbeddings()))
    
    def find_visually_similar_images_to_image(self, img: Image, k: int=100) -> list[SearchResult]:
        return self.image_similarity_calculator.compute_similarity(self._embed_image(img), k)
    
    def update_description_embedding(self, file: FileMetadata, old_description: str):
        self._update_text_embedding(file, old_description, file.description, self.description_similarity_calculator, StoredEmbeddingType.DESCRIPTION)

    def update_transcript_embedding(self, file: FileMetadata, old_transcript: str):
        self._update_text_embedding(file, old_transcript, file.transcript, self.transcription_text_similarity_calculator, StoredEmbeddingType.TRANSCRIPTION_TEXT)

    async def on_file_created(self, file: FileMetadata):
        # since this is a new file created at runtime there should be no description
        embeddings = StoredEmbeddings()
        if file.file_type == FileType.IMAGE:
            self.image_similarity_calculator.add(file.id, self._create_image_embedding(file, embeddings))
            self.clip_image_similarity_calculator.add(file.id, self._create_clip_image_embedding(file, embeddings))
        if file.file_type == FileType.VIDEO:
            if await self._create_clip_video_embeddings(file, embeddings) is not None:
                self.clip_video_similarity_calculator.add(file.id, embeddings.clip_video)
        if file.is_screenshot and file.is_ocr_analyzed:
            self._create_text_embedding(file.ocr_text, embeddings, StoredEmbeddingType.OCR_TEXT)
            self.ocr_text_similarity_calculator.add(file.id, embeddings.ocr_text.embedding)
        if file.is_transcript_analyzed and file.transcript is not None:
            self._create_text_embedding(file.transcript, embeddings, StoredEmbeddingType.TRANSCRIPTION_TEXT)
            self.transcription_text_similarity_calculator.add(file.id, embeddings.transcription_text.embedding)
        self.persistor.save(file.name, embeddings)

    async def on_file_deleted(self, file: FileMetadata):
        self.persistor.delete(file.name)
        if file.file_type == FileType.IMAGE:
            self.clip_image_similarity_calculator.delete(file.id)
            self.image_similarity_calculator.delete(file.id)
        if file.file_type == FileType.VIDEO:
            self.clip_video_similarity_calculator.delete(file.id)
        if file.is_ocr_analyzed:
            self.ocr_text_similarity_calculator.delete(file.id)
        if file.is_transcript_analyzed:
            self.transcription_text_similarity_calculator.delete(file.id)
        self.description_similarity_calculator.delete(file.id)

    def _update_text_embedding(self, file: FileMetadata, old_text: str, new_text: str, calc: EmbeddingSimilarityCalculator, embedding_type: StoredEmbeddingType):
        embeddings = self.persistor.load_without_consistency_check(file.name)
        fid = int(file.id)
        if new_text != '':    
            embedding = self._create_text_embedding(new_text, embeddings, embedding_type)
            self.persistor.save(file.name, embeddings)
            if old_text == '':
                calc.add(fid, embedding)
            else:
                calc.replace(fid, embedding)
        else:
            calc.delete(fid)
        
    def _find_similar_items(self,
        file: FileMetadata,
        k: int,
        calculator: EmbeddingSimilarityCalculator,
        embedding_provider: Callable[[], np.ndarray]
    ) -> list[SearchResult]:
        this = SearchResult(item_id=file.id, score=1.)
        emb = calculator.get_embedding(file.id)
        add_this = False
        if emb is None:
            emb = embedding_provider()
            add_this = True
        res = calculator.compute_similarity(emb, k)
        if add_this:
            res = [this, *emb]
        return res
    
    def _create_text_embedding(self, text: str, embeddings: StoredEmbeddings, embedding_type: StoredEmbeddingType) -> np.ndarray:
        res = self._create_mutable_text_embedding(text)
        embeddings[embedding_type] = res
        return res.embedding

    def _create_description_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray: 
        embeddings.description = self._create_mutable_text_embedding(file.description)
        return embeddings.description.embedding
    
    def _create_transcription_text_embeddings(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        embeddings.transcription_text = self._create_mutable_text_embedding(file.transcript)
        return embeddings.transcription_text.embedding
    
    def _create_mutable_text_embedding(self, text: str) -> MutableTextEmbedding:
        with self.text_embedding_engine.run() as engine:
            return MutableTextEmbedding(text=text, embedding=engine.generate_passage_embedding(text))
    
    def _create_image_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        img = Image.open(self.root_dir.joinpath(file.name)).convert('RGB')
        embeddings.image = self._embed_image(img)
        return embeddings.image
    
    def _create_clip_image_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        img = Image.open(self.root_dir.joinpath(file.name)).convert('RGB')
        with self.clip_engine.run() as engine:
            embeddings.clip_image = engine.generate_image_embedding(img)
        return embeddings.clip_image
    
    async def _create_clip_video_embeddings(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray: 
        try:
            video_duration = get_video_duration_seconds(self.root_dir.joinpath(file.name))
            with self.clip_engine.run() as engine:
                frame_embeddings = []
                for i in range(self.num_clip_video_frames):
                    # TODO smarter frame selection
                    offset = video_duration * ((2 * i + 1) / (2 * self.num_clip_video_frames))
                    img = get_video_frame_at_offset(self.root_dir.joinpath(file.name), offset)
                    frame_embeddings.append(engine.generate_image_embedding(img))
                embeddings.clip_video = np.vstack(frame_embeddings)
            return embeddings.clip_image
        except Exception as e:
            logger.error(f'failed to generate clip video embeddings for file: {file.name}', exc_info=e)
            # TODO clean this up
            file_refreshed = await self.file_repo.get_file_by_id(file.id)
            file_refreshed.has_video_embedding_failed = True
            await self.file_repo.update_file(file_refreshed)
            return None

    def _embed_image(self, image: Image.Image) -> np.ndarray:
        with self.image_embedding_engine.run() as engine:
            return engine.generate_image_embedding(image)
