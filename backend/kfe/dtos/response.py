
from typing import Optional

from pydantic import BaseModel, Field

from kfe.persistence.model import FileType


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
    is_transcript_fixed: Optional[bool]

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

class GetOffsetOfFileInLoadResultsResponse(BaseModel):
    idx: int

class RegisteredDirectoryDTO(BaseModel):
    name: str
    ready: bool
    failed: bool
    init_progress_description: str = Field(default='Unknown initialization progress')
    init_progress: float = Field(default=0.)

class SelectDirectoryResponse(BaseModel):
    selected_path: Optional[str]
    canceled: bool
