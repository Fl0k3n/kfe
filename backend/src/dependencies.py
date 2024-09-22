
from pathlib import Path

from dtos.mappers import Mapper
from features.ocr_engine import OCREngine
from features.transcriber import Transcriber
from persistence.db import Database
from persistence.embeddings import EmbeddingPersistor
from persistence.file_metadata_repository import FileMetadataRepository
from search.image_embedding_engine import ImageEmbeddingEngine
from search.lemmatizer import Lemmatizer
from search.query_parser import SearchQueryParser
from search.text_embedding_engine import TextEmbeddingEngine
from service.embedding_processor import EmbeddingProcessor
from service.file_indexer import FileIndexer
from service.metadata_editor import MetadataEditor
from service.ocr_service import OCRService
from service.search import SearchService
from service.thumbnails import ThumbnailManager
from service.transcription_service import TranscriptionService
from utils.lexical_search_engine_initializer import \
    LexicalSearchEngineInitializer
from utils.log import logger
from utils.persistence import dump_descriptions, restore_descriptions

# from spacy.lang.pl import Polish


# ROOT_DIR = Path('/home/flok3n/minikonrad'); DB_DIR = Path('.')
ROOT_DIR = Path('/home/flok3n/konrad'); DB_DIR = ROOT_DIR

db = Database(DB_DIR)
file_repo = FileMetadataRepository(db)
file_indexer = FileIndexer(ROOT_DIR, file_repo)
thumbnail_manager = ThumbnailManager(ROOT_DIR)

mapper = Mapper(thumbnail_manager)


# tokenizer = Tokenizer(vocab=Polish())
lemmatizer = Lemmatizer()
lexical_search_initializer = LexicalSearchEngineInitializer(lemmatizer, file_repo)

text_embedding_engine = TextEmbeddingEngine()
image_embedding_engine = ImageEmbeddingEngine()
embedding_persistor = EmbeddingPersistor(ROOT_DIR)
embedding_processor = EmbeddingProcessor(ROOT_DIR, embedding_persistor, text_embedding_engine, image_embedding_engine)

ocr_engine = OCREngine()
ocr_service = OCRService(ROOT_DIR, file_repo, ocr_engine)

transcriber = Transcriber()
transcription_service = TranscriptionService(ROOT_DIR, transcriber, file_repo)

query_parser = SearchQueryParser()

search_service = SearchService(
    file_repo,
    query_parser,
    lexical_search_initializer.description_lexical_search_engine,
    lexical_search_initializer.ocr_text_lexical_search_engine,
    lexical_search_initializer.transcript_lexical_search_engine,
    embedding_processor,
)

metadata_editor = MetadataEditor(file_repo, lexical_search_initializer.description_lexical_search_engine, embedding_processor)
        
async def init(should_dump_descriptions=False, should_restore_descriptions=False):
    logger.info('initializing database')
    await db.init_db()

    logger.info('ensuring directory initialized')
    num_previously_stored_files = await file_indexer.ensure_directory_initialized()

    description_dump_path = ROOT_DIR.joinpath('description_dump.json')
    if should_restore_descriptions:
        logger.info(f'restoring descriptions from {description_dump_path}')
        await restore_descriptions(description_dump_path, db)
    if num_previously_stored_files > 0 and should_dump_descriptions:
        logger.info(f'dumping descriptions to {description_dump_path}')
        await dump_descriptions(description_dump_path, file_repo)

    logger.info('initializing OCR services')
    await ocr_service.init_ocrs()

    logger.info('initializing transcription services')
    await transcription_service.init_transcriptions()

    logger.info('initializing lexical search engines')
    await lexical_search_initializer.init_search_engines()

    logger.info('initalizing embeddings')
    embedding_processor.init_embeddings(await file_repo.load_all_files())

    logger.info('application ready')

async def teardown():
    await db.close_db()

def get_file_repo() -> FileMetadataRepository:
    return file_repo

def get_thumbnail_manager() -> ThumbnailManager:
    return thumbnail_manager

def get_search_service() -> SearchService:
    return search_service

def get_mapper() -> Mapper:
    return mapper

def get_metadata_editor() -> MetadataEditor:
    return metadata_editor
