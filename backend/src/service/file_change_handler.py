from pathlib import Path

from persistence.db import Database
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileType
from service.embedding_processor import EmbeddingProcessor
from service.file_indexer import FileIndexer
from service.ocr_service import OCRService
from service.thumbnails import ThumbnailManager
from service.transcription_service import TranscriptionService
from utils.log import logger


class FileChangeHandler:
    def __init__(self, file_repo: FileMetadataRepository, file_indexer: FileIndexer,
                 embedding_processor: EmbeddingProcessor, ocr_service: OCRService,
                transcription_service: TranscriptionService, thumbnail_manager: ThumbnailManager):
        self.file_repo = file_repo
        self.file_indexer = file_indexer
        self.embedding_processor = embedding_processor
        self.ocr_servce = ocr_service
        self.transcription_service = transcription_service
        self.thumbnail_manager = thumbnail_manager

    async def on_file_created(self, path: Path):
        if not self._should_handle_path(path):
            return
        logger.info(f'handling new file at: {path}')
        file = await self.file_indexer.add_file(path)
        if file is None:
            return
        if file.file_type == FileType.IMAGE:
            self.ocr_servce.perform_ocr(file)
        if file.file_type in (FileType.AUDIO, FileType.VIDEO):
            await self.transcription_service.transcribe_file(file)
        await self.embedding_processor.on_file_created(file)
        await self.thumbnail_manager.on_file_created(file)
        await self.file_repo.update_file(file)
        logger.info(f'file ready for querying: {path}')

    async def on_file_deleted(self, path: Path):
        if not self._should_handle_path(path):
            return
        file = await self.file_indexer.delete_file(path)
        if file is None:
            return
        logger.info(f'handling file deleted from: {path}')
        await self.embedding_processor.on_file_deleted(file)
        self.thumbnail_manager.on_file_deleted(file)

    def _should_handle_path(self, path: Path) -> bool:
        return path.name != f'{Database.DB_FILE_NAME}-journal'