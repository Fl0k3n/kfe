
from pathlib import Path

from persistence.db import Database
from persistence.file_metadata_repository import FileMetadataRepository
from service.file_indexer import FileIndexer

ROOT_DIR = Path('/home/flok3n/minikonrad')
# DB_DIR = ROOT_DIR
DB_DIR = Path('.')

db = Database(DB_DIR)
file_repo = FileMetadataRepository(db)
file_indexer = FileIndexer(ROOT_DIR, file_repo)


async def init():
    await db.init_db()
    await file_indexer.ensure_directory_initialized()

async def teardown():
    await db.close_db()

def get_file_repo() -> FileMetadataRepository:
    return file_repo
