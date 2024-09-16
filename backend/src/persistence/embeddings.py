import hashlib
import io
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import NamedTuple, Optional

import numpy as np


class StoredEmbeddingType(str, Enum):
    DESCRIPTION = "D"
    IMAGE = "I"

@dataclass(frozen=False)
class DescriptionEmbedding:
    text: str
    embedding: Optional[np.ndarray] = None

@dataclass(frozen=False)
class StoredEmbeddings:
    description: Optional[DescriptionEmbedding] = None
    image: Optional[np.ndarray] = None

    def get_key(self) -> str:
        res = ""
        if self.description is not None:
            res += StoredEmbeddingType.DESCRIPTION
        if self.image is not None:
            res += StoredEmbeddingType.IMAGE
        return res
    
    def without(self, emb_type: StoredEmbeddingType) -> "StoredEmbeddings":
        res = StoredEmbeddings(**asdict(self))
        if emb_type == StoredEmbeddingType.DESCRIPTION:
            res.description = None
        elif emb_type == StoredEmbeddingType.IMAGE:
            res.image = None
        return res

class EmbeddingPersistor:
    HASH_LENGTH = 32
    EMBEDDING_FILE_EXTENSION = '.emb'

    def __init__(self, root_dir: Path) -> None:
        self.embedding_dir = root_dir.joinpath('.embeddings')
        try:
            os.mkdir(self.embedding_dir)
        except FileExistsError:
            pass

        self.serializers = {
            StoredEmbeddingType.DESCRIPTION: self._serialize_description,
            StoredEmbeddingType.IMAGE: self._serialize_image
        }
        self.deserializers = {
            StoredEmbeddingType.DESCRIPTION: self._deserialize_description,
            StoredEmbeddingType.IMAGE: self._deserialize_image
        }

    def save(self, file_name: str, embeddings: StoredEmbeddings):
        path = self._get_file_path(file_name)
        key = embeddings.get_key()
        if not key:
            if path.exists():
                self.delete(file_name)
            return
        with open(path, 'wb') as f:
            f.write(str(len(key)).encode('ascii'))
            f.write(key.encode('ascii'))
            for embedding_type in key:
                self.serializers[embedding_type](f, embeddings)

    def load(self, file_name: str, expected_description: str) -> StoredEmbeddings:
        res = StoredEmbeddings(description=DescriptionEmbedding(embedding=None, text=expected_description))
        try:
            with open(self._get_file_path(file_name), 'rb') as f:
                key_size = int(f.read(1).decode('ascii'))
                key = f.read(key_size).decode('ascii')
                for embedding_type in key:
                    self.deserializers[embedding_type](f, res)
            return res
        except Exception as e:
            print(e)
            return StoredEmbeddings()

    def delete(self, file_name: str):
        os.remove(self._get_file_path(file_name))
        
    def get_all_embedded_files(self) -> list[str]:
        return [x.name[:-len(self.EMBEDDING_FILE_EXTENSION)] for x in self.embedding_dir.iterdir()]
        
    def _serialize_description(self, f: io.BufferedWriter, embeddings: StoredEmbeddings):
        if embeddings.description is None or embeddings.description.embedding is None:
            return
        description_hash = self._hash_text_to_embed(embeddings.description.text)
        f.write(description_hash)
        np.save(f, embeddings.description.embedding, allow_pickle=False)

    def _serialize_image(self, f: io.BufferedWriter, embeddings: StoredEmbeddings):
        if embeddings.image is None:
            return
        np.save(f, embeddings.image, allow_pickle=False)

    def _deserialize_description(self, f: io.BufferedReader, embeddings: StoredEmbeddings):
        text_hash = f.read(self.HASH_LENGTH)
        if self._is_hash_valid(text_hash, embeddings.description.text):
            embeddings.description.embedding = np.load(f, allow_pickle=False)
        else:
            embeddings.description = None
    
    def _deserialize_image(self, f: io.BufferedReader, embeddings: StoredEmbeddings) -> StoredEmbeddings:
        embeddings.image = np.load(f, allow_pickle=False)

    def _hash_text_to_embed(self, text: str) -> bytes:
        text_hash = hashlib.sha256(str(text).encode(), usedforsecurity=False).digest()
        assert len(text_hash) == self.HASH_LENGTH
        return text_hash

    def _is_hash_valid(self, hash: bytes, text: str) -> bool:
        text_hash = self._hash_text_to_embed(text)
        return text_hash == hash

    def _get_file_path(self, file_name: str) -> Path:
        return self.embedding_dir.joinpath(file_name + self.EMBEDDING_FILE_EXTENSION)
