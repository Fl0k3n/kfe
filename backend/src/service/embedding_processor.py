from pathlib import Path
from typing import Callable, Optional

import numpy as np
from PIL import Image

from persistence.embeddings import (EmbeddingPersistor, MutableTextEmbedding,
                                    StoredEmbeddings, StoredEmbeddingType)
from persistence.model import FileMetadata, FileType
from search.embedding_similarity_calculator import \
    EmbeddingSimilarityCalculator
from search.image_embedding_engine import ImageEmbeddingEngine
from search.models import SearchResult
from search.text_embedding_engine import TextEmbeddingEngine


class EmbeddingProcessor:
    HASH_LENGTH = 32
    EMBEDDING_FILE_EXTENSION = '.emb'

    def __init__(self, root_dir: Path, persistor: EmbeddingPersistor,
                 text_embedding_engine: TextEmbeddingEngine,
                 image_embedding_engine: ImageEmbeddingEngine) -> None:
        self.root_dir = root_dir
        self.persistor = persistor
        self.text_embedding_engine = text_embedding_engine
        self.image_embedding_engine = image_embedding_engine
            
        self.description_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.image_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.ocr_text_similarity_calculator: EmbeddingSimilarityCalculator = None 
        self.transcription_text_similarity_calculator: EmbeddingSimilarityCalculator = None 

    def init_embeddings(self, all_files: list[FileMetadata]):
        files_by_name = {str(x.name): x for x in all_files}
        description_builder = EmbeddingSimilarityCalculator.Builder()
        image_builder = EmbeddingSimilarityCalculator.Builder()
        ocr_text_builder = EmbeddingSimilarityCalculator.Builder()
        transcription_text_builder = EmbeddingSimilarityCalculator.Builder()
         
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
                    self._create_description_embedding(file, embeddings)
                    dirty = True
                if file.file_type == FileType.IMAGE and embeddings.image is None:
                    self._create_image_embedding(file, embeddings)
                    dirty = True
                if file.is_screenshot and file.is_ocr_analyzed and embeddings.ocr_text is None:
                    self._create_ocr_text_embedding(file, embeddings)
                    dirty = True
                if file.is_transcript_analyzed and file.transcript is not None and embeddings.transcription_text is None:
                    self._create_transcription_text_embeddings(file, embeddings)
                    dirty = True

                if embeddings.description is not None:
                    description_builder.add_row(file.id, embeddings.description.embedding)
                if embeddings.image is not None:
                    image_builder.add_row(file.id, embeddings.image)
                if embeddings.ocr_text is not None:
                    ocr_text_builder.add_row(file.id, embeddings.ocr_text.embedding)
                if embeddings.transcription_text is not None:
                    transcription_text_builder.add_row(file.id, embeddings.transcription_text.embedding)

                if dirty:
                    self.persistor.save(file.name, embeddings)

        for file in files_by_name.values():
            embeddings = StoredEmbeddings()
            if file.description != '':
                self._create_description_embedding(file, embeddings)
                description_builder.add_row(file.id, embeddings.description.embedding)
            if file.file_type == FileType.IMAGE:
                self._create_image_embedding(file, embeddings)
                image_builder.add_row(file.id, embeddings.image)
            if file.is_screenshot and file.is_ocr_analyzed:
                self._create_ocr_text_embedding(file, embeddings)
                ocr_text_builder.add_row(file.id, embeddings.ocr_text.embedding)
            if file.is_transcript_analyzed and file.transcript is not None:
                self._create_transcription_text_embeddings(file, embeddings)
                transcription_text_builder.add_row(file.id, embeddings.transcription_text.embedding)
            self.persistor.save(file.name, embeddings)

        self.description_similarity_calculator = description_builder.build()
        self.image_similarity_calculator = image_builder.build()
        self.ocr_text_similarity_calculator = ocr_text_builder.build()
        self.transcription_text_similarity_calculator= transcription_text_builder.build()

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
    
    def find_items_with_similar_descriptions(self, file: FileMetadata, k: int=10) -> list[SearchResult]:
        if file.description == '':
            return SearchResult(item_id=file.id, score=1.)
        return self._find_similar_items(file, k, self.description_similarity_calculator,
             lambda: self._create_description_embedding(file, StoredEmbeddings()))
    
    def find_visually_similar_images(self, file: FileMetadata, k: int=10) -> list[SearchResult]:
        if file.file_type != FileType.IMAGE:
            return SearchResult(item_id=file.id, score=1.)
        return self._find_similar_items(file, k, self.image_similarity_calculator,
             lambda: self._create_image_embedding(file, StoredEmbeddings()))
    
    def update_description_embedding(self, file: FileMetadata, old_description: str):
        embeddings = self.persistor.load_without_consistency_check(file.name)
        fid = int(file.id)
        if file.description != '':    
            embedding = self._create_description_embedding(file, embeddings)
            self.persistor.save(file.name, embeddings)
            if old_description == '':
                self.description_similarity_calculator.add(fid, embedding)
            else:
                self.description_similarity_calculator.replace(fid, embedding)
        else:
            self.description_similarity_calculator.delete(fid)

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

    def _create_description_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray: 
        embeddings.description = self._create_mutable_text_embedding(file.description)
        return embeddings.description.embedding
    
    def _create_ocr_text_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        embeddings.ocr_text = self._create_mutable_text_embedding(file.ocr_text)
        return embeddings.ocr_text.embedding
    
    def _create_transcription_text_embeddings(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        embeddings.transcription_text = self._create_mutable_text_embedding(file.transcript)
        return embeddings.transcription_text.embedding
    
    def _create_mutable_text_embedding(self, text: str) -> MutableTextEmbedding:
        with self.text_embedding_engine.run() as engine:
            return MutableTextEmbedding(text=text, embedding=engine.generate_passage_embedding(text))
    
    def _create_image_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        img = Image.open(self.root_dir.joinpath(file.name)).convert('RGB')
        with self.image_embedding_engine.run() as engine:
            embeddings.image = engine.generate_image_embedding(img)
        return embeddings.image
