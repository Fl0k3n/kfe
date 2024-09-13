
from pathlib import Path

from dtos.mappers import Mapper
from persistence.db import Database
from persistence.file_metadata_repository import FileMetadataRepository
from search.embedding_engine import EmbeddingEngine
from search.lemmatizer import Lemmatizer
from search.lexical_search_engine import LexicalSearchEngine
from search.reverse_index import ReverseIndex
from search.token_stat_counter import TokenStatCounter
from service.embedding_processor import EmbeddingProcessor
from service.file_indexer import FileIndexer
from service.search import SearchService
from service.thumbnails import ThumbnailManager
from utils.persistence import dump_descriptions, restore_descriptions

# from spacy.lang.pl import Polish


ROOT_DIR = Path('/home/flok3n/minikonrad')
# DB_DIR = ROOT_DIR
DB_DIR = Path('.')

db = Database(DB_DIR)
file_repo = FileMetadataRepository(db)
file_indexer = FileIndexer(ROOT_DIR, file_repo)
thumbnail_manager = ThumbnailManager(ROOT_DIR)

mapper = Mapper(thumbnail_manager)


# tokenizer = Tokenizer(vocab=Polish())
lemmatizer = Lemmatizer()
description_reverse_index = ReverseIndex()
description_token_stat_counter = TokenStatCounter()
description_lexical_search_engine = LexicalSearchEngine(lemmatizer, description_reverse_index, description_token_stat_counter)

embedding_engine = EmbeddingEngine()
embedding_processor = EmbeddingProcessor(ROOT_DIR, embedding_engine)

search_service = SearchService(description_lexical_search_engine, embedding_processor, file_repo)

async def init_description_lexical_search_engine():
    files = await file_repo.load_all_files()
    for file in files:
        tokens = lemmatizer.lemmatize(file.description)
        for token in tokens:
            description_reverse_index.add_entry(token, int(file.id))
        description_token_stat_counter.register(tokens, int(file.id))


async def init(should_dump_descriptions=False, should_restore_descriptions=False):
    await db.init_db()
    num_previously_stored_files = await file_indexer.ensure_directory_initialized()
    if should_restore_descriptions:
        await restore_descriptions(ROOT_DIR.joinpath('description_dump.json'), db)
    if num_previously_stored_files > 0 and should_dump_descriptions:
        await dump_descriptions(ROOT_DIR.joinpath('description_dump.json'), file_repo)
    await init_description_lexical_search_engine()
    embedding_processor.init_embeddings(await file_repo.load_all_files())

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
