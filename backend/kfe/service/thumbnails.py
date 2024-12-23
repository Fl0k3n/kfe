import asyncio
import base64
import io
import os
from pathlib import Path

import aiofiles
from lru import LRU
from PIL import Image, ImageOps

from kfe.persistence.model import FileMetadata, FileType
from kfe.utils.init_progress_tracker import InitProgressTracker, InitState
from kfe.utils.log import logger
from kfe.utils.video_frames_extractor import (get_video_duration_seconds,
                                              seconds_to_ffmpeg_time)


class ThumbnailManager:
    THUMBNAIL_FILE_EXTENSION = '.tn'

    def __init__(self, root_dir: Path, thumbnails_dir_name: str='.thumbnails', size: int=300, cache_item_limit=5000) -> None:
        self.root_dir = root_dir
        self.thumbnails_dir = root_dir.joinpath(thumbnails_dir_name)
        self.thumbnail_size = size
        self.thumbnail_cache: dict[str, str] = LRU(cache_item_limit)
        try:
            os.mkdir(self.thumbnails_dir)
        except FileExistsError:
            pass

    async def preload_thumbnails(self, files: list[FileMetadata], progress_tracker: InitProgressTracker):
        progress_tracker.enter_state(InitState.THUMBNAILS, len(files))
        for f in files:
            await self.get_encoded_file_thumbnail(f)
            progress_tracker.mark_file_processed()

    def remove_thumbnails_of_deleted_files(self, existing_files: list[FileMetadata]):
        file_names = set(str(file.name) for file in existing_files)
        for item in os.scandir(self.thumbnails_dir):
            if self._get_original_file_name_from_thumbnail_path(Path(item.path)) not in file_names:
                self._remove_thumbnail(item.path)

    async def get_encoded_file_thumbnail(self, file: FileMetadata) -> str:
        thumbnail = self.thumbnail_cache.get(str(file.name))
        if thumbnail is not None:
            return thumbnail
        if file.file_type not in (FileType.IMAGE, FileType.VIDEO):
            return ""
        try:
            file_path = self.root_dir.joinpath(file.name)
            preprocessed_thumbnail_path = self._get_preprocessed_thumbnail_path(file)
            recreate = True
            if preprocessed_thumbnail_path.exists():
                try:
                    buff = await self._load_preprocessed_thumbnail(preprocessed_thumbnail_path)
                    recreate = False
                except Exception as e:
                    logger.warning('failed to load preprocessed thumbnail', exc_info=e)
            if recreate:
                logger.debug(f'creating preprocessed thumbnail for {file.name}')
                if file.file_type == FileType.VIDEO:
                    buff = await self._create_video_thumbnail(file_path)
                else:
                    buff = await self._create_image_thumbnail(file_path)
                await self._write_preprocessed_thumbnail(preprocessed_thumbnail_path, buff)
            thumbnail = base64.b64encode(buff.getvalue()).decode()
            self.thumbnail_cache[str(file.name)] = thumbnail
            return thumbnail
        except Exception as e:
            logger.debug(f'Failed to get file thumbnail for file: {file.name}', exc_info=e)
            return ""
        
    async def on_file_created(self, file: FileMetadata):
        await self.get_encoded_file_thumbnail(file)

    def on_file_deleted(self, file: FileMetadata):
        self.thumbnail_cache.pop(str(file.name), None)
        if file.file_type in (FileType.VIDEO, FileType.IMAGE):
            self._remove_thumbnail(self._get_preprocessed_thumbnail_path(file))

    def _remove_thumbnail(self, path: Path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f'Failed to remove thumbnail from {path}', exc_info=e)

    async def _create_video_thumbnail(self, path: Path, size: int=300) -> io.BytesIO:
        ss = '00:00:01.00'
        for i in range(2):
            proc = await asyncio.subprocess.create_subprocess_exec(
                'ffmpeg',
                *['-ss', ss,
                '-i', str(path.absolute()),
                '-vframes', '1',
                '-vf', f'scale={size}:{size}:force_original_aspect_ratio=decrease',
                '-f', 'mjpeg', '-'],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                return io.BytesIO(stdout)
            if i == 0:
                video_duration = await get_video_duration_seconds(path)
                ss = seconds_to_ffmpeg_time(video_duration / 2)
            else:
                logger.warning(f'ffmpeg returned with {proc.returncode} code for thumbnail generation for {path.name}')
                logger.debug(f'ffmpeg stderr: {stderr.decode()}')
                return io.BytesIO(stdout) # try anyway, probably will raise
    
    async def _create_image_thumbnail(self, path: Path, size: int=300) -> io.BytesIO:
        async with aiofiles.open(path, 'rb') as f:
            data = await f.read()
        buff = io.BytesIO()
        img = Image.open(io.BytesIO(data)).convert('RGB')
        img = ImageOps.contain(img, size=(size, size))
        img.save(buff, format="JPEG")
        return buff
    
    async def _load_preprocessed_thumbnail(self, path: Path) -> io.BytesIO:
        async with aiofiles.open(path, 'rb') as f:
            return io.BytesIO(await f.read())

    async def _write_preprocessed_thumbnail(self, path: Path, data: io.BytesIO):
        async with aiofiles.open(path, 'wb') as f:
            await f.write(data.getvalue())

    def _get_preprocessed_thumbnail_path(self, file: FileMetadata) -> Path:
        return self.thumbnails_dir.joinpath('.' + file.name + self.THUMBNAIL_FILE_EXTENSION)

    def _get_original_file_name_from_thumbnail_path(self, path: Path) -> str:
        try:
            return path.name[1:-len(self.THUMBNAIL_FILE_EXTENSION)]
        except:
            return path.name
