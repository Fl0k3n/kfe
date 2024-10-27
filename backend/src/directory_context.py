
import asyncio
import os
from pathlib import Path

import torch

from features.clip_engine import CLIPEngine
from features.image_embedding_engine import ImageEmbeddingEngine
from features.ocr_engine import OCREngine
from features.text_embedding_engine import TextEmbeddingEngine
from features.transcriber import Transcriber
from persistence.db import Database
from persistence.embeddings import EmbeddingPersistor
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileType
from search.lemmatizer import Lemmatizer
from service.embedding_processor import EmbeddingProcessor
from service.file_indexer import FileIndexer
from service.ocr_service import OCRService
from service.thumbnails import ThumbnailManager
from service.transcription_service import TranscriptionService
from utils.constants import PRELOAD_THUMBNAILS_ENV
from utils.file_change_watcher import FileChangeWatcher
from utils.lexical_search_engine_initializer import \
    LexicalSearchEngineInitializer
from utils.log import logger
from utils.model_manager import ModelManager, ModelType


class DirectoryContext:
    def __init__(self, root_dir: Path, db_dir: Path, model_manager: ModelManager, lemmatizer: Lemmatizer, languages: list[str]):
        self.root_dir = root_dir
        self.db_dir = db_dir
        self.model_manager = model_manager
        self.lemmatizer = lemmatizer
        self.languages = languages
        self.init_lock = asyncio.Lock()
        self.db: Database = None

        self.context_ready = False 
        self.init_queue: list[tuple[Path, bool]] = []

    async def init_directory_context(self, device: torch.device):
        async with self.init_lock:
            self.db = Database(self.db_dir)
            self.thumbnail_manager = ThumbnailManager(self.root_dir)
            self.ocr_engine = OCREngine(self.model_manager, self.languages)
            self.transcriber = Transcriber(self.model_manager)
            self.embedding_persistor = EmbeddingPersistor(self.root_dir)

            self.text_embedding_engine = TextEmbeddingEngine(self.model_manager)
            self.image_embedding_engine = ImageEmbeddingEngine(self.model_manager, device)
            self.clip_engine = CLIPEngine(self.model_manager, device)
            self.embedding_processor = EmbeddingProcessor(self.root_dir, self.embedding_persistor, self.text_embedding_engine, self.image_embedding_engine, self.clip_engine)

            logger.info(f'initializing database for {self.root_dir}')
            await self.db.init_db()

            async with self.db.session() as sess:
                async with sess.begin():
                    file_repo = FileMetadataRepository(sess)
                    file_indexer = FileIndexer(self.root_dir, file_repo)
                    ocr_service = OCRService(self.root_dir, file_repo, self.ocr_engine)
                    transcription_service = TranscriptionService(self.root_dir, self.transcriber, file_repo)
                    self.lexical_search_initializer = LexicalSearchEngineInitializer(self.lemmatizer, file_repo)
                    self.file_change_watcher = FileChangeWatcher(self.root_dir, self._on_file_created, self._on_file_deleted, self._on_file_moved,
                            ignored_files=set([Database.DB_FILE_NAME, f'{Database.DB_FILE_NAME}-journal']))

                    logger.info(f'initializg file change watcher for directory: {self.root_dir}')
                    self.file_change_watcher.start_watcher_thread(asyncio.get_running_loop())

                    logger.info(f'ensuring directory {self.root_dir} initialized')
                    await file_indexer.ensure_directory_initialized()

                    logger.info(f'initializing OCR services for directory {self.root_dir}')
                    await ocr_service.init_ocrs()

                    logger.info(f'initializing transcription services for directory {self.root_dir}')
                    await transcription_service.init_transcriptions(retranscribe_all_auto_trancribed=False)

                    logger.info(f'initializing lexical search engines for directory {self.root_dir}')
                    await self.lexical_search_initializer.init_search_engines()

                    logger.info(f'initalizing embeddings for directory {self.root_dir}')
                    with (
                        self.model_manager.use(ModelType.TEXT_EMBEDDING),
                        self.model_manager.use(ModelType.IMAGE_EMBEDDING),
                        self.model_manager.use(ModelType.CLIP)
                    ):
                        await self.embedding_processor.init_embeddings(file_repo)
                    
                    if os.getenv(PRELOAD_THUMBNAILS_ENV, 'false') == 'true':
                        logger.info(f'preloading thumbnails for directory {self.root_dir}')
                        await self.thumbnail_manager.preload_thumbnails(await file_repo.load_all_files())

                    logger.info(f'directory {self.root_dir} ready')
                    await self._directory_context_initialized()

    async def teardown_directory_context(self):
        async with self.init_lock:
            if self.file_change_watcher is not None:
                self.file_change_watcher.stop()
            if self.db is not None:
                await self.db.close_db()

    async def _directory_context_initialized(self):
        self.context_ready = True
        for path, is_create in self.init_queue:
            if is_create:
                await self._on_file_created(path)
            else:
                await self._on_file_deleted(path)

    async def _on_file_created(self, path: Path):
        if not self.context_ready:
            self.init_queue.append((path, True))
            return

        logger.info(f'handling new file at: {path}')
        async with self.db.session() as sess:
            async with sess.begin():
                file_repo = FileMetadataRepository(sess)
                file_indexer = FileIndexer(self.root_dir, file_repo)
                file = await file_indexer.add_file(path)
                if file is None:
                    return
                if file.file_type == FileType.IMAGE:
                    OCRService(self.root_dir, file_repo, self.ocr_engine).perform_ocr(file)
                if file.file_type in (FileType.AUDIO, FileType.VIDEO):
                    await TranscriptionService(self.root_dir, self.transcriber, file_repo).transcribe_file(file)
                await self.embedding_processor.on_file_created(file)
                await self.thumbnail_manager.on_file_created(file)
                await file_repo.update_file(file)
                logger.info(f'file ready for querying: {path}')

    async def _on_file_deleted(self, path: Path):
        if not self.context_ready:
            self.init_queue.append((path, False))
            return

        async with self.db.session() as sess:
            async with sess.begin():
                file_repo = FileMetadataRepository(sess)
                file_indexer = FileIndexer(self.root_dir, file_repo)
                file = await file_indexer.delete_file(path)
                if file is None:
                    return
                logger.info(f'handling file deleted from: {path}')
                await self.embedding_processor.on_file_deleted(file)
                self.thumbnail_manager.on_file_deleted(file)

    async def _on_file_moved(self, old_path: Path, new_path: Path):
        await self._on_file_deleted(old_path)
        if new_path.parent.name == self.root_dir.name:
            await self._on_file_created(new_path)


class DirectoryContextHolder:
    def __init__(self, model_manager: ModelManager, lemmatizer: Lemmatizer, device: torch.device):
        self.model_manager = model_manager
        self.lemmatizer = lemmatizer
        self.device = device
        self.context_change_lock = asyncio.Lock()
        self.contexts: dict[str, DirectoryContext] = {}
        self.init_failed_contexts: set[str] = set()
        self.stopped = False

    async def register_directory(self, name: str, root_dir: Path, languages: list[str]):
        async with self.context_change_lock:
            assert not self.stopped
            assert name not in self.contexts
            if not root_dir.exists():
                self.init_failed_contexts.add(name)
                raise FileNotFoundError(f'directory {name} does not exist at {root_dir}')
            if name in self.init_failed_contexts:
                self.init_failed_contexts.remove(name)
            ctx = DirectoryContext(root_dir, root_dir, self.model_manager, self.lemmatizer, languages)
            try:
                await ctx.init_directory_context(self.device)
            except Exception:
                await ctx.teardown_directory_context()
                self.init_failed_contexts.add(name)
                raise
            self.contexts[name] = ctx

    async def unregister_directory(self, name: str):
        async with self.context_change_lock:
            ctx = self.contexts.pop(name)
            await ctx.teardown_directory_context()

    def has_context(self, name: str) -> bool:
        return name in self.contexts
    
    def has_init_failed(self, name: str) -> bool:
        return name in self.init_failed_contexts

    def get_context(self, name: str) -> DirectoryContext:
        return self.contexts[name]

    async def teardown(self):
        async with self.context_change_lock:
            self.stopped = True
            for name, ctx in self.contexts.items():
                try:
                    await ctx.teardown_directory_context()
                except Exception as e:
                    logger.error(f'failed to to teardown directory context for directory {name}', exc_info=e)

