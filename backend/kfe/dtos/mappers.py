from kfe.dtos.response import FileMetadataDTO, SearchResultDTO
from kfe.persistence.model import FileMetadata
from kfe.search.models import AggregatedSearchResult
from kfe.service.thumbnails import ThumbnailManager


class Mapper:
    def __init__(self, thumbnail_manager: ThumbnailManager) -> None:
        self.thumbnail_manager = thumbnail_manager

    async def file_metadata_to_dto(self, file: FileMetadata) -> FileMetadataDTO:
        return FileMetadataDTO(
            id=file.id,
            name=file.name,
            description=file.description,
            added_at=str(file.added_at),
            file_type=file.file_type,
            thumbnail_base64=await self.thumbnail_manager.get_encoded_file_thumbnail(file),
            is_screenshot=file.is_screenshot,
            ocr_text=file.ocr_text,
            transcript=str(file.transcript) if file.is_transcript_analyzed and file.transcript is not None else None,
            is_transcript_fixed=file.is_transcript_fixed if file.transcript is not None else None
        )

    async def aggregated_search_result_to_dto(self, asr: AggregatedSearchResult) -> SearchResultDTO:
        return SearchResultDTO(
            file=await self.file_metadata_to_dto(asr.file),
            dense_score=asr.dense_score,
            lexical_score=asr.lexical_score,
            total_score=asr.total_score
        )
