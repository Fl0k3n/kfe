from dtos.response import FileMetadataDTO
from persistence.model import FileMetadata


def file_metadata_to_dto(md: FileMetadata, thumbnail_base64: str) -> FileMetadataDTO:
    return FileMetadataDTO(
        id=md.id,
        name=md.name,
        description=md.description,
        added_at=str(md.added_at),
        file_type=md.file_type,
        thumbnail_base64=thumbnail_base64
    )
