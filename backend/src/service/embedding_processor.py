from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from persistence.embeddings import (DescriptionEmbedding, EmbeddingPersistor,
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

    def init_embeddings(self, all_files: list[FileMetadata]):
        files_by_name = {str(x.name): x for x in all_files}
        description_builder = EmbeddingSimilarityCalculator.Builder()
        image_builder = EmbeddingSimilarityCalculator.Builder()

        for file_name in self.persistor.get_all_embedded_files():
            file = files_by_name.pop(file_name, None)
            if file is None:
                self.persistor.delete(file_name)
            else:
                dirty = False
                embeddings = self.persistor.load(file_name, expected_description=file.description)
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

                if embeddings.description is not None:
                    description_builder.add_row(file.id, embeddings.description.embedding)
                if embeddings.image is not None:
                    image_builder.add_row(file.id, embeddings.image)

                if dirty:
                    self.persistor.save(file.name, embeddings)


        for file in files_by_name.values():
            embeddings = StoredEmbeddings()
            if file.description != '':
                self._create_description_embedding(file, embeddings)
                description_builder.add_row(file.id, embeddings.description.embedding)
            if file.file_type == FileType.IMAGE:
                self._create_image_embedding(file, embeddings)
            self.persistor.save(file.name, embeddings)

        self.description_similarity_calculator = description_builder.build()
        self.image_similarity_calculator = image_builder.build()

    def search_description_based(self, query: str, k: int=10) -> list[SearchResult]:
        query_embedding = self.text_embedding_engine.generate_query_embedding(query)
        return self.description_similarity_calculator.compute_similarity(query_embedding, k)
    
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
        embeddings.description = DescriptionEmbedding(
            text=file.description,
            embedding=self.text_embedding_engine.generate_passage_embedding(file.description)
        )
        return embeddings.description.embedding
    
    def _create_image_embedding(self, file: FileMetadata, embeddings: StoredEmbeddings) -> np.ndarray:
        img = Image.open(self.root_dir.joinpath(file.name)).convert('RGB')
        embeddings.image = self.image_embedding_engine.generate_image_embedding(img)
        return embeddings.image
