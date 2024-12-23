import hashlib
import io
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional, get_args

import numpy as np

from kfe.utils.log import logger


class StoredEmbeddingType(str, Enum):
    DESCRIPTION        = "D"
    OCR_TEXT           = "O"
    TRANSCRIPTION_TEXT = "T"
    CLIP_IMAGE         = "C"
    CLIP_VIDEO         = "V"

@dataclass(frozen=False)
class MutableTextEmbedding:
    text: str
    embedding: Optional[np.ndarray] = None

@dataclass(frozen=False)
class StoredEmbeddings:
    description: Annotated[Optional[MutableTextEmbedding], StoredEmbeddingType.DESCRIPTION] = None
    ocr_text: Annotated[Optional[MutableTextEmbedding], StoredEmbeddingType.OCR_TEXT] = None
    transcription_text: Annotated[Optional[MutableTextEmbedding], StoredEmbeddingType.TRANSCRIPTION_TEXT] = None
    clip_image: Annotated[Optional[np.ndarray], StoredEmbeddingType.CLIP_IMAGE] = None
    clip_video: Annotated[Optional[np.ndarray], StoredEmbeddingType.CLIP_VIDEO] = None

    def __getitem__(self, key: StoredEmbeddingType):
        for field_name, annotation in self.__annotations__.items():
            if get_args(annotation)[1] == key:
                return self.__dict__[field_name]
        raise KeyError(key)
    
    def __setitem__(self, key: StoredEmbeddingType, val):
        for field_name, annotation in self.__annotations__.items():
            if get_args(annotation)[1] == key:
                self.__dict__[field_name] = val
                return
        raise KeyError(key)

    def get_key(self) -> str:
        res = ""
        for emb_type in StoredEmbeddingType:
            if self[emb_type] is not None:
                res += emb_type
        return res
    
    def without(self, emb_type: StoredEmbeddingType) -> "StoredEmbeddings":
        res = StoredEmbeddings(**asdict(self))
        res[emb_type] = None
        return res
    
    @classmethod
    def get_annotation_for(cls, key: StoredEmbeddingType) -> Annotated:
        for annotation in cls.__annotations__.values():
            field_type, emb_type = get_args(annotation)
            if emb_type == key:
                return field_type
        raise KeyError(key)

class EmbeddingPersistor:
    HASH_LENGTH = 32
    EMBEDDING_FILE_EXTENSION = '.emb'

    def __init__(self, root_dir: Path) -> None:
        self.embedding_dir = root_dir.joinpath('.embeddings')
        try:
            os.mkdir(self.embedding_dir)
        except FileExistsError:
            pass

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
                field_type, field_value = get_args(StoredEmbeddings.get_annotation_for(embedding_type))[0], embeddings[embedding_type]
                if field_type == MutableTextEmbedding:
                    self._serialize_mutable_text(f, field_value)
                elif field_type == np.ndarray:
                    self._serialize_embedding_vector(f, field_value)

    def load(self, file_name: str, expected_texts: dict[StoredEmbeddingType, str]) -> StoredEmbeddings:
        res = StoredEmbeddings()
        try:
            with open(self._get_file_path(file_name), 'rb') as f:
                key_size = int(f.read(1).decode('ascii'))
                key = f.read(key_size).decode('ascii')
                for embedding_type in key:
                    field_type = get_args(StoredEmbeddings.get_annotation_for(embedding_type))[0]
                    if field_type == MutableTextEmbedding:
                        res[embedding_type] = self._deserialize_mutable_text(f, expected_texts[embedding_type])
                    elif field_type == np.ndarray:
                        res[embedding_type] = self._deserialize_embedding_vector(f)
            return res
        except Exception as e:
            logger.error(f'failed to load embeddings for {file_name}', exc_info=e)
            return StoredEmbeddings()
        
    def load_without_consistency_check(self, file_name: str) -> StoredEmbeddings:
        return self.load(file_name, expected_texts={x: None for x in StoredEmbeddingType})
        
    def delete(self, file_name: str):
        try:
            os.remove(self._get_file_path(file_name))
        except FileNotFoundError:
            pass
        
    def get_all_embedded_files(self) -> list[str]:
        res = []
        for x in self.embedding_dir.iterdir():
            try:
                if x.name.endswith(self.EMBEDDING_FILE_EXTENSION):
                    res.append(x.name[1:-len(self.EMBEDDING_FILE_EXTENSION)])
            except:
                pass
        return res
    
    def _serialize_mutable_text(self, f: io.BufferedWriter, mutable_text: Optional[MutableTextEmbedding]):
        if mutable_text is None or mutable_text.embedding is None:
            return
        description_hash = self._hash_text_to_embed(mutable_text.text)
        f.write(description_hash)
        self._serialize_embedding_vector(f, mutable_text.embedding)

    def _deserialize_mutable_text(self, f: io.BufferedReader, expected_text: Optional[str]) -> Optional[MutableTextEmbedding]:
        text_hash = f.read(self.HASH_LENGTH)
        embedding_vector = self._deserialize_embedding_vector(f)
        if expected_text is None or self._is_hash_valid(text_hash, expected_text):
            return MutableTextEmbedding(text=expected_text, embedding=embedding_vector)
        return None 

    def _serialize_embedding_vector(self, f: io.BufferedWriter, vec: Optional[np.ndarray]):
        if vec is None:
            return
        np.save(f, vec, allow_pickle=False)

    def _deserialize_embedding_vector(self, f: io.BufferedReader) -> np.ndarray:
        return np.load(f, allow_pickle=False)

    def _hash_text_to_embed(self, text: str) -> bytes:
        text_hash = hashlib.sha256(str(text).encode(), usedforsecurity=False).digest()
        assert len(text_hash) == self.HASH_LENGTH
        return text_hash

    def _is_hash_valid(self, hash: bytes, text: str) -> bool:
        text_hash = self._hash_text_to_embed(text)
        return text_hash == hash

    def _get_file_path(self, file_name: str) -> Path:
        return self.embedding_dir.joinpath("." + file_name + self.EMBEDDING_FILE_EXTENSION)
