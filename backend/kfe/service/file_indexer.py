import io
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from PIL import Image

from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata, FileType
from kfe.utils.ffprobe import (get_ffprobe_stream_info, has_audio_stream,
                               has_video_stream)
from kfe.utils.log import logger


class FileIndexer:
    def __init__(self, root_dir: Path, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.file_repo = file_repo

    async def ensure_directory_initialized(self) -> int:
        stored_files = await self.file_repo.load_all_files()
        actual_files = self.load_directory_files()

        names_of_stored_files = set(str(x.name) for x in stored_files)
        names_of_actual_files = set(actual_files)

        new_files = names_of_actual_files.difference(names_of_stored_files)
        if file_names_to_delete := names_of_stored_files.difference(names_of_actual_files):
            logger.info('some files were deleted, cleaning database')
            await self.file_repo.delete_files([x for x in stored_files if x.name in file_names_to_delete] )

        files_to_create = []
        for filename in new_files:
            try:
                path = self.root_dir.joinpath(filename)
                if file_metadata := await self._build_file_metadata(path):
                    files_to_create.append(file_metadata)
            except Exception as e:
                logger.error(f'failed to add file metadata for: {path}', exc_info=e)

        if files_to_create:
            await self.file_repo.add_all(files_to_create)
            logger.info(f'created {len(files_to_create)} files; database had {len(stored_files)} files; directory has {len(actual_files)} files')
        else:
            logger.info('no new files, database ready')
        
        return len(stored_files)
    
    async def update_file_types(self):
        stored_files = await self.file_repo.load_all_files()
        for file in stored_files:
            actual_file_type = await FileIndexer.get_file_type(self.root_dir.joinpath(file.name))
            if file.file_type != actual_file_type:
                file.ftype = actual_file_type
    
    async def add_file(self, path: Path) -> Optional[FileMetadata]:
        try:
            file = await self._build_file_metadata(path)
            if file is None:
                return None
            await self.file_repo.add(file)
            return file
        except Exception as e:
            logger.error(f'failed to add file from: {path}', exc_info=e)
            return None

    async def delete_file(self, path: Path) -> Optional[FileMetadata]:
        file = await self.file_repo.get_file_by_name(path.name)
        if file is None:
            return None
        await self.file_repo.delete_files([file])
        return file

    async def _build_file_metadata(self, path: Path) -> FileMetadata | None:
        file_type = await FileIndexer.get_file_type(path)
        if file_type == FileType.OTHER:
            return None
        creation_time = datetime.fromtimestamp(path.stat().st_ctime)
        return FileMetadata(
            name=path.name,
            added_at=creation_time,
            description="",
            ftype=file_type
        )

    def load_directory_files(self) -> list[str]:
        res = []
        for entry in self.root_dir.iterdir():
            if entry.is_file():
                res.append(entry.name)
        return res

    @staticmethod
    async def get_file_type(path: Path) -> FileType:
        mime_type = mimetypes.guess_type(path.name)[0]
        if mime_type is None:
            if path.name.endswith('.webp'):
                mime_type = 'image'
            else:
                return FileType.OTHER
        if mime_type.startswith('image'):
            try:
                async with aiofiles.open(path, 'rb') as f:
                    Image.open(io.BytesIO(await f.read()))
                return FileType.IMAGE
            except:
                return FileType.OTHER
        if mime_type.startswith('video') or mime_type.startswith('audio'):
            ffprobe_info = await get_ffprobe_stream_info(path)
            if ffprobe_info is None:
                return FileType.OTHER
            if has_video_stream(ffprobe_info):
                return FileType.VIDEO
            elif has_audio_stream(ffprobe_info):
                return FileType.AUDIO
        return FileType.OTHER
