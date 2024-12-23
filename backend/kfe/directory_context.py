
import asyncio
import os
from pathlib import Path
from typing import Optional

import torch

from kfe.features.clip_engine import CLIPEngine
from kfe.features.lemmatizer import Lemmatizer
from kfe.features.ocr_engine import OCREngine
from kfe.features.text_embedding_engine import TextEmbeddingEngine
from kfe.features.transcriber import PipelineBasedTranscriber
from kfe.persistence.db import Database
from kfe.persistence.embeddings import EmbeddingPersistor
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileType
from kfe.search.query_parser import SearchQueryParser
from kfe.service.embedding_processor import EmbeddingProcessor
from kfe.service.file_indexer import FileIndexer
from kfe.service.metadata_editor import MetadataEditor
from kfe.service.ocr_service import OCRService
from kfe.service.search import SearchService
from kfe.service.thumbnails import ThumbnailManager
from kfe.service.transcription_service import TranscriptionService
from kfe.utils.constants import (LOG_SQL_ENV, PRELOAD_THUMBNAILS_ENV,
                                 RETRANSCRIBE_AUTO_TRANSCRIBED_ENV, Language)
from kfe.utils.file_change_watcher import FileChangeWatcher
from kfe.utils.hybrid_search_confidence_providers import \
    HybridSearchConfidenceProviderFactory
from kfe.utils.init_progress_tracker import InitProgressTracker
from kfe.utils.lexical_search_engine_initializer import \
    LexicalSearchEngineInitializer
from kfe.utils.log import logger
from kfe.utils.model_manager import ModelManager, ModelType


class DirectoryContext:
    def __init__(self, root_dir: Path, db_dir: Path, model_manager: ModelManager,
                 hybrid_search_confidence_provider_factory: HybridSearchConfidenceProviderFactory,
                 primary_language: Language, init_progress_tracker: InitProgressTracker):
        self.root_dir = root_dir
        self.db_dir = db_dir
        self.model_manager = model_manager
        self.hybrid_search_confidence_provider_factory = hybrid_search_confidence_provider_factory
        self.primary_language = primary_language
        self.init_lock = asyncio.Lock()
        self.init_progress_tracker = init_progress_tracker
        self.db: Database = None
        self.file_change_watcher: FileChangeWatcher = None

        self.context_ready = False 
        self.init_queue: list[tuple[Path, bool]] = []
        self.paths_waiting_for_deletion: set[Path] = set()
        self.file_creation_in_progress_paths: set[Path] = set()

    async def init_directory_context(self, device: torch.device):
        async with self.init_lock:
            self.db = Database(self.db_dir, log_sql=os.getenv(LOG_SQL_ENV, 'false') == 'true')
            self.thumbnail_manager = ThumbnailManager(self.root_dir)
            self.lemmatizer = Lemmatizer(self.model_manager)
            self.ocr_engine = OCREngine(self.model_manager, ['en'] if self.primary_language == 'en' else [self.primary_language, 'en'])
            self.transcriber = PipelineBasedTranscriber(self.model_manager)
            self.embedding_persistor = EmbeddingPersistor(self.root_dir)

            self.text_embedding_engine = TextEmbeddingEngine(self.model_manager)
            self.clip_engine = CLIPEngine(self.model_manager, device)
            self.embedding_processor = EmbeddingProcessor(self.root_dir, self.embedding_persistor, self.text_embedding_engine, self.clip_engine)

            logger.debug(f'initializing database for {self.root_dir}')
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

                    logger.debug(f'initializg file change watcher for directory: {self.root_dir}')
                    self.file_change_watcher.start_watcher_thread(asyncio.get_running_loop())

                    logger.info(f'ensuring directory {self.root_dir} initialized')
                    await file_indexer.ensure_directory_initialized()

                    logger.info(f'initializing OCR services for directory {self.root_dir}')
                    await ocr_service.init_ocrs(self.init_progress_tracker)

                    logger.info(f'initializing transcription services for directory {self.root_dir}')
                    await transcription_service.init_transcriptions(self.init_progress_tracker,
                        retranscribe_all_auto_trancribed=os.getenv(RETRANSCRIBE_AUTO_TRANSCRIBED_ENV, 'false') == 'true')

                    logger.info(f'initializing lexical search engines for directory {self.root_dir}')
                    await self.lexical_search_initializer.init_search_engines(self.init_progress_tracker, 
                        relemmatize_transcriptions=os.getenv(RETRANSCRIBE_AUTO_TRANSCRIBED_ENV, 'false') == 'true')

                    logger.info(f'initalizing embeddings for directory {self.root_dir}')
                    async with (
                        self.model_manager.use(ModelType.TEXT_EMBEDDING),
                        self.model_manager.use(ModelType.CLIP)
                    ):
                        await self.embedding_processor.init_embeddings(file_repo, self.init_progress_tracker)
                    
                    self.thumbnail_manager.remove_thumbnails_of_deleted_files(await file_repo.load_all_files())
                    if os.getenv(PRELOAD_THUMBNAILS_ENV, 'true') == 'true':
                        logger.debug(f'preloading thumbnails for directory {self.root_dir}')
                        await self.thumbnail_manager.preload_thumbnails(await file_repo.load_all_files(), self.init_progress_tracker)

                    if str(device) == 'cuda':
                        torch.cuda.empty_cache()

                    logger.info(f'directory {self.root_dir} ready')
                    await self._directory_context_initialized()

    async def teardown_directory_context(self):
        async with self.init_lock:
            if self.file_change_watcher is not None:
                self.file_change_watcher.stop()
            if self.db is not None:
                await self.db.close_db()

    def get_metadata_editor(self, file_repo: FileMetadataRepository) -> MetadataEditor:
        return MetadataEditor(
            file_repo,
            self.lexical_search_initializer.description_lexical_search_engine,
            self.lexical_search_initializer.transcript_lexical_search_engine,
            self.lexical_search_initializer.ocr_text_lexical_search_engine,
            self.embedding_processor,
            self.lemmatizer
        )
    
    def get_search_service(self, file_repo: FileMetadataRepository) -> SearchService:
        return SearchService(
            file_repo,
            SearchQueryParser(),
            self.lexical_search_initializer.description_lexical_search_engine,
            self.lexical_search_initializer.ocr_text_lexical_search_engine,
            self.lexical_search_initializer.transcript_lexical_search_engine,
            self.embedding_processor,
            self.lemmatizer,
            self.hybrid_search_confidence_provider_factory,
            include_clip_in_hybrid_search=self.primary_language == 'en', # clip model requires english queries
        )

    async def _directory_context_initialized(self):
        self.context_ready = True
        for path, is_create in self.init_queue:
            if is_create:
                await self._on_file_created(path)
            else:
                await self._on_file_deleted(path)
        self.init_progress_tracker.set_ready()

    async def _on_file_created(self, path: Path):
        if not self.context_ready:
            self.init_queue.append((path, True))
            return
        
        self.file_creation_in_progress_paths.add(path)
        try:
            logger.info(f'handling new file at: {path}')
            async with self.db.session() as sess:
                async with sess.begin():
                    file_repo = FileMetadataRepository(sess)
                    file_indexer = FileIndexer(self.root_dir, file_repo)
                    file = await file_indexer.add_file(path)
                    if file is None:
                        return
                    if file.file_type == FileType.IMAGE:
                        await OCRService(self.root_dir, file_repo, self.ocr_engine).perform_ocr(file)
                    if file.file_type in (FileType.AUDIO, FileType.VIDEO):
                        await TranscriptionService(self.root_dir, self.transcriber, file_repo).transcribe_file(file)
                    await self.embedding_processor.on_file_created(file)
                    await self.get_metadata_editor(file_repo).on_file_created(file)
                    await self.thumbnail_manager.on_file_created(file)
                    await file_repo.update_file(file)
                    logger.info(f'file ready for querying: {path}')
        finally:
            self.file_creation_in_progress_paths.remove(path)
            if path in self.paths_waiting_for_deletion:
                self.paths_waiting_for_deletion.remove(path)
                await self._on_file_deleted(path)

    async def _on_file_deleted(self, path: Path):
        if not self.context_ready:
            self.init_queue.append((path, False))
            return
        
        if path in self.file_creation_in_progress_paths:
            self.paths_waiting_for_deletion.add(path)
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
                await self.get_metadata_editor(file_repo).on_file_deleted(file)
                self.thumbnail_manager.on_file_deleted(file)

    async def _on_file_moved(self, old_path: Path, new_path: Path):
        await self._on_file_deleted(old_path)
        if new_path.parent.name == self.root_dir.name:
            await self._on_file_created(new_path)


class DirectoryContextHolder:
    def __init__(self,
            model_managers: dict[Language, ModelManager],
            hybrid_search_confidence_provider_factories: dict[Language, HybridSearchConfidenceProviderFactory],
            device: torch.device):
        self.model_managers = model_managers
        self.hybrid_search_confidence_provider_factories = hybrid_search_confidence_provider_factories
        self.device = device
        self.context_change_lock = asyncio.Lock()
        self.contexts: dict[str, DirectoryContext] = {}
        self.init_progress_trackers: dict[str, InitProgressTracker] = {}
        self.init_failed_contexts: set[str] = set()
        self.stopped = False
        self.initialized = False
        self.directory_init_background_tasks: set[asyncio.Task] = set()

    def set_initialized(self):
        self.initialized = True

    def is_initialized(self) -> bool:
        return self.initialized

    async def register_directory(self, name: str, root_dir: Path, primary_language: Language):
        async with self.context_change_lock:
            assert not self.stopped
            assert name not in self.contexts
            if not root_dir.exists():
                self.init_failed_contexts.add(name)
                raise FileNotFoundError(f'directory {name} does not exist at {root_dir}')
            if name in self.init_failed_contexts:
                self.init_failed_contexts.remove(name)
            progress_tracker = InitProgressTracker()
            self.init_progress_trackers[name] = progress_tracker
            ctx = DirectoryContext(root_dir, root_dir, self.model_managers[primary_language],
                self.hybrid_search_confidence_provider_factories[primary_language], primary_language, progress_tracker)
            try:
                await ctx.init_directory_context(self.device)
            except Exception as e:
                if 'CUDA out of memory' in str(e):
                    logger.error(
                        f'Unrecoverable GPU out of memory error occured while initializing directory {name}. ' +
                         'Consider running the application with --cpu flag.'
                    )
                await ctx.teardown_directory_context()
                self.init_failed_contexts.add(name)
                raise
            self.contexts[name] = ctx
            self.init_progress_trackers.pop(name)

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
    
    def get_init_progress(self, name: str) -> Optional[tuple[str, float]]:
        if tracker := self.init_progress_trackers.get(name):
            return tracker.get_progress_status()
        return None

    async def teardown(self):
        for task in list(self.directory_init_background_tasks):
            task.cancel()
        async with self.context_change_lock:
            self.stopped = True
            for name, ctx in self.contexts.items():
                try:
                    await ctx.teardown_directory_context()
                except Exception as e:
                    logger.error(f'failed to to teardown directory context for directory {name}', exc_info=e)

