import asyncio
from datetime import datetime
from pathlib import Path

import magic

from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata, FileType
from utils.log import logger


class FileIndexer:
    def __init__(self, root_dir: Path, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.file_repo = file_repo

    async def ensure_directory_initialized(self) -> int:
        stored_files = await self.file_repo.load_all_files()
        actual_files = await self.load_directory_files()

        names_of_stored_files = set(str(x.name) for x in stored_files)
        names_of_actual_files = set(actual_files)

        new_files = names_of_actual_files.difference(names_of_stored_files)
        if file_names_to_delete := names_of_stored_files.difference(names_of_actual_files):
            logger.info('some files were deleted, cleaning database')
            self.file_repo.delete_files([x for x in stored_files if x.name in file_names_to_delete] )

        files_to_create = []
        for filename in new_files:
            try:
                path = self.root_dir.joinpath(filename)
                file_type = FileIndexer.get_file_type(path)
                if file_type == FileType.OTHER:
                    continue
                creation_time = datetime.fromtimestamp(path.stat().st_ctime)
                files_to_create.append(FileMetadata(
                    name=filename,
                    added_at=creation_time,
                    description="",
                    ftype=file_type
                ))
            except Exception as e:
                print(e)

        if files_to_create:
            await self.file_repo.add_all(files_to_create)
            logger.info(f'created {len(files_to_create)} files; database had {len(stored_files)} files; directory has {len(actual_files)} files')
        else:
            logger.info('no new files, database ready')
        
        return len(stored_files)


    async def load_directory_files(self) -> list[str]:
        def load() -> list[str]:
            res = []
            for entry in self.root_dir.iterdir():
                if entry.is_file():
                    res.append(entry.name)
            return res
        return await asyncio.get_running_loop().run_in_executor(None, load)


    @staticmethod
    def get_file_type(path: Path) -> FileType:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(path)
        if mime_type.startswith('image'):
            return FileType.IMAGE
        if mime_type.startswith('video'):
            return FileType.VIDEO
        if mime_type.startswith('audio'):
            return FileType.AUDIO
        return FileType.OTHER
