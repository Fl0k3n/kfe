
from typing import Optional

from pydantic import BaseModel

from persistence.model import FileType


class FileMetadataDTO(BaseModel):
    id: int
    name: str
    added_at: str
    description: str
    file_type: FileType
    thumbnail_base64: str

    is_screenshot: bool
    ocr_text: Optional[str]

    transcript: Optional[str]

class SearchResultDTO(BaseModel):
    file: FileMetadataDTO
    dense_score: float
    lexical_score: float
    total_score: float


class PaginatedResponse(BaseModel):
    offset: int
    total: int

class LoadAllFilesResponse(PaginatedResponse):
    files: list[FileMetadataDTO]

class SearchResponse(PaginatedResponse):
    results: list[SearchResultDTO]


class GetIdxOfFileResponse(BaseModel):
    idx: int
