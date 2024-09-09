from sqlalchemy import desc, select

from persistence.db import Database
from persistence.model import FileMetadata


class FileMetadataRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def load_all_files(self) -> list[FileMetadata]:
        async with self.db.session() as sess:
            files = await sess.execute(select(FileMetadata).order_by(desc(FileMetadata.added_at)))
            return list(files.scalars().all())

    async def update_description(self, file_id: int, description: str):
        async with self.db.session() as sess:
            async with sess.begin():
                file = await sess.get_one(FileMetadata, file_id)
                file.description = description

    async def add_all(self, files: list[FileMetadata]):
        async with self.db.session() as sess:
            async with sess.begin():
                sess.add_all(files)

                