from typing import Optional

from sqlalchemy import desc, func, select

from persistence.db import Database
from persistence.model import FileMetadata


class FileMetadataRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_file_by_id(self, file_id: int) -> Optional[FileMetadata]:
        async with self.db.session() as sess:
            result = await sess.execute(
                select(FileMetadata).where(FileMetadata.id == file_id)
            )
            return result.scalars().first()

    async def load_all_files(self) -> list[FileMetadata]:
        async with self.db.session() as sess:
            files = await sess.execute(select(FileMetadata).order_by(desc(FileMetadata.added_at)))
            return list(files.scalars().all())
        
    async def get_number_of_files(self) -> int:
        async with self.db.session() as sess:
            res = await sess.execute(select(func.count()).select_from(FileMetadata))
            return res.scalar() or 0
        
    async def load_files(self, offset: int, limit: Optional[int]=None) -> list[FileMetadata]:
        async with self.db.session() as sess:
            files = await sess.execute(select(FileMetadata).order_by(desc(FileMetadata.added_at)).offset(offset).limit(limit))
            return list(files.scalars().all())
    
    async def delete_files(self, items: list[FileMetadata]):
        async with self.db.session() as sess:
            async with sess.begin():
                for item in items:
                    await sess.delete(item)

    async def update_description(self, file_id: int, description: str):
        async with self.db.session() as sess:
            async with sess.begin():
                file = await sess.get_one(FileMetadata, file_id)
                file.description = description

    async def add_all(self, files: list[FileMetadata]):
        async with self.db.session() as sess:
            async with sess.begin():
                sess.add_all(files)

    async def get_files_with_ids(self, ids: set[int]) -> list[FileMetadata]:
        all_files = await self.load_all_files()
        return [f for f in all_files if int(f.id) in ids]

    async def get_files_with_ids_by_id(self, ids: set[int]) -> dict[int, FileMetadata]:
        all_files = await self.load_all_files()
        return {int(f.id): f for f in all_files if int(f.id) in ids}
    