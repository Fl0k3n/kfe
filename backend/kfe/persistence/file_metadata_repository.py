from typing import Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from kfe.persistence.model import FileMetadata, FileType


class FileMetadataRepository:
    def __init__(self, sess: AsyncSession) -> None:
        self.sess = sess

    async def get_file_by_id(self, file_id: int) -> Optional[FileMetadata]:
        result = await self.sess.execute(
            select(FileMetadata).where(FileMetadata.id == file_id)
        )
        return result.scalars().first()
        
    async def get_file_by_name(self, name: str) -> Optional[FileMetadata]:
        result = await self.sess.execute(
            select(FileMetadata).where(FileMetadata.name == name)
        )
        return result.scalars().first()

    async def get_number_of_files(self) -> int:
        res = await self.sess.execute(select(func.count()).select_from(FileMetadata))
        return res.scalar() or 0
        
    async def load_files(self, offset: int, limit: Optional[int]=None) -> list[FileMetadata]:
        files = await self.sess.execute(select(FileMetadata).order_by(desc(FileMetadata.added_at), desc(FileMetadata.id)).offset(offset).limit(limit))
        return list(files.scalars().all())
    
    async def get_file_offset_within_sorted_results(self, file_id: int) -> int:
        file = await self.get_file_by_id(file_id)
        if file is None:
            return 0
        offset_query = await self.sess.execute(
            select(func.count())
            .select_from(FileMetadata)
            .where(or_(
                FileMetadata.added_at > file.added_at,
                and_(
                    FileMetadata.added_at == file.added_at,
                    FileMetadata.id > file_id
                )
            ))
        )
        offset = offset_query.scalar()
        return offset if offset is not None else 0

    async def load_all_files(self) -> list[FileMetadata]:
        return await self.load_files(0, limit=None)
    
    async def delete_files(self, items: list[FileMetadata]):
        async with self.sess.begin_nested():
            for item in items:
                await self.sess.delete(item)

    async def update_description(self, file_id: int, description: str):
        async with self.sess.begin_nested():
            file = await self.sess.get_one(FileMetadata, file_id)
            file.description = description

    async def update_file(self, file: FileMetadata):
        async with self.sess.begin_nested():
            self.sess.add(file)

    async def add(self, file: FileMetadata):
        async with self.sess.begin_nested():
            self.sess.add(file)

    async def add_all(self, files: list[FileMetadata]):
        async with self.sess.begin_nested():
            self.sess.add_all(files)

    async def get_files_with_ids(self, ids: set[int]) -> list[FileMetadata]:
        all_files = await self.load_all_files()
        return [f for f in all_files if int(f.id) in ids]

    async def get_files_with_ids_by_id(self, ids: set[int]) -> dict[int, FileMetadata]:
        all_files = await self.load_all_files()
        return {int(f.id): f for f in all_files if int(f.id) in ids}
    
    async def get_all_images_with_not_analyzed_ocr(self) -> list[FileMetadata]:
        files = await self.sess.execute(
            select(FileMetadata).
            where((FileMetadata.ftype == FileType.IMAGE.value) & (FileMetadata.is_ocr_analyzed == False))
        )
        return list(files.scalars().all())

    async def get_all_audio_files_with_not_analyzed_trancription(self) -> list[FileMetadata]:
        files = await self.sess.execute(
            select(FileMetadata).
            where(
                ((FileMetadata.ftype == FileType.VIDEO.value) | (FileMetadata.ftype == FileType.AUDIO.value)) &
                (FileMetadata.is_transcript_analyzed == False))
        )
        return list(files.scalars().all())

    async def get_all_audio_files_with_not_manually_fixed_transcript(self) -> list[FileMetadata]:
        files = await self.sess.execute(
            select(FileMetadata).
            where(
                ((FileMetadata.ftype == FileType.VIDEO.value) | (FileMetadata.ftype == FileType.AUDIO.value)) &
                (FileMetadata.is_transcript_fixed == False))
        )
        return list(files.scalars().all())
