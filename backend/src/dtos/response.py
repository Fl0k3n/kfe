
from pydantic import BaseModel

from persistence.model import FileType


class FileMetadataDTO(BaseModel):
    id: int
    name: str
    added_at: str
    description: str
    file_type: FileType
    thumbnail_base64: str


class SearchResultDTO(BaseModel):
    file: FileMetadataDTO
    dense_score: float
    lexical_score: float
    total_score: float
