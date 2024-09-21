import asyncio
import base64
import io
import os
from pathlib import Path

import aiofiles
from PIL import Image, ImageOps

from persistence.model import FileMetadata, FileType
from utils.log import logger


class ThumbnailManager:
    def __init__(self, root_dir: Path, thumbnails_dir_name: str='.thumbnails', size: int=300) -> None:
        self.root_dir = root_dir
        self.thumbnails_dir = root_dir.joinpath(thumbnails_dir_name)
        self.thumbnail_size = size
        self.thumbnail_cache = {}
        try:
            os.mkdir(self.thumbnails_dir)
        except FileExistsError:
            pass

    async def get_encoded_file_thumbnail(self, file: FileMetadata) -> str:
        thumbnail = self.thumbnail_cache.get(file.name)
        if thumbnail is not None:
            return thumbnail
        try:
            file_path = self.root_dir.joinpath(file.name)
            if file.file_type == FileType.AUDIO:
                return ""
            if file.file_type == FileType.IMAGE:
                buff = await self._create_image_thumbnail(file_path, size=self.thumbnail_size)
            elif file.file_type == FileType.VIDEO:
                preprocessed_thumbnail_path = self.thumbnails_dir.joinpath(file.name)
                recreate = True
                if preprocessed_thumbnail_path.exists():
                    try:
                        buff = await self._load_preprocessed_thumbnail(preprocessed_thumbnail_path)
                        recreate = False
                    except Exception as e:
                        logger.warning('failed to load preprocessed thumbnail', exc_info=e)
                if recreate:
                    logger.debug(f'creating preprocessed video thumbnail for {file.name}')
                    buff = await self._create_video_thumbnail(file_path)
                    await self._write_preprocessed_thumbnail(preprocessed_thumbnail_path, buff)
            else:
                return ""
            thumbnail = base64.b64encode(buff.getvalue()).decode()
            self.thumbnail_cache[file.name] = thumbnail
            return thumbnail
        except Exception as e:
            logger.error(f'Failed to get file thumbnail for file: {file.name}', exc_info=e)
            return ""

    async def _create_video_thumbnail(self, path: Path, size: int=300) -> io.BytesIO:
        proc = await asyncio.subprocess.create_subprocess_exec(
            'ffmpeg',
            *['-ss', '00:00:01.00',
            '-i', str(path.absolute()),
            '-vframes', '1',
            '-vf', f'scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:black',
            '-f', 'singlejpeg', '-'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f'ffmpeg returned with {proc.returncode} code for thumbnail generation for {path.name}')
            logger.debug(f'ffmpeg stderr: {stderr.decode()}')
        return io.BytesIO(stdout)
    
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
