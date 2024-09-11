import hashlib
import os
from pathlib import Path
from typing import NamedTuple, Optional

import numpy as np

from persistence.model import FileMetadata
from search.embedding_engine import EmbeddingEngine


class SimilarityResult(NamedTuple):
    item_id: int
    similarity: float # in range [-1, 1]

class EmbeddingProcessor:
    HASH_LENGTH = 32

    def __init__(self, root_dir: Path, embedding_engine: EmbeddingEngine) -> None:
        self.embedding_engine = embedding_engine
        self.embedding_dir = root_dir.joinpath('.embeddings')
        try:
            os.mkdir(self.embedding_dir)
        except FileExistsError:
            pass
            
        self.row_to_file_id: list[int] = []
        self.embedding_matrix: np.ndarray = None

    def init_embeddings(self, all_files: list[FileMetadata]):
        rows = []
        self.row_to_file_id = []
        files_by_name = {str(x.name): x for x in all_files}

        for entry in self.embedding_dir.iterdir():
            file = files_by_name.pop(entry.name, None)
            if file is None or file.description == '':
                os.remove(entry)
            else:
                embedding = self._decode_and_validate_embedding(entry, file.description)
                if embedding is None:
                    embedding = self.register_description(file)
                rows.append(embedding)
                self.row_to_file_id.append(file.id)

        for file in files_by_name.values():
            if file.description != '':
                embedding = self.register_description(file)
                rows.append(embedding)
                self.row_to_file_id.append(int(file.id))

        self.embedding_matrix = np.vstack(rows)

    def register_description(self, file: FileMetadata) -> np.ndarray:
        embedding_path = self.embedding_dir.joinpath(file.name)
        if file.description == '':
            if embedding_path.exists():
                try:
                    os.remove(embedding_path)
                except Exception as e:
                    print(e)
            return None
        embedding = self.embedding_engine.generate_passage_embedding(file.description)
        with open(embedding_path, 'wb') as f:
            f.write(self._hash_text_to_embed(str(file.description)))
            np.save(f, embedding, allow_pickle=False)
        return embedding
            
    def find_most_similar_items(self, query: str, k: int=10) -> list[SimilarityResult]:
        query_embedding = self.embedding_engine.generate_query_embedding(query)
        similarities = query_embedding @ self.embedding_matrix.T
        sorted_by_similarity_asc = np.argsort(similarities)
        res = []
        for i in range(len(sorted_by_similarity_asc) - 1, len(sorted_by_similarity_asc) - k - 1, -1):
            res.append(SimilarityResult(
                item_id=sorted_by_similarity_asc[i],
                similarity=similarities[sorted_by_similarity_asc[i]]
            ))
        return res

    def _hash_text_to_embed(self, text: str) -> bytes:
        text_hash = hashlib.sha256(str(text).encode(), usedforsecurity=False).digest()
        assert len(text_hash) == self.HASH_LENGTH
        return text_hash

    def _is_hash_valid(self, hash: bytes, text: str) -> bool:
        text_hash = self._hash_text_to_embed(text)
        return text_hash == hash
    
    def _decode_and_validate_embedding(self, path: Path, expected_text: str) -> Optional[np.ndarray]:
        try:
            with open(path, 'rb') as f:
                text_hash = f.read(self.HASH_LENGTH)
                if not self._is_hash_valid(text_hash, expected_text):
                    return None
                return np.load(f, allow_pickle=False)
        except Exception as e:
            print(e)
            return None
