import asyncio
import base64
import io
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from PIL import Image

from dependencies import ROOT_DIR, get_file_repo
from dtos.mappers import file_metadata_to_dto
from dtos.response import FileMetadataDTO
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata, FileType

router = APIRouter(prefix="/load")

async def get_video_thumbnail(path: Path, size: int=300) -> io.BytesIO:
    s = size
    proc = await asyncio.subprocess.create_subprocess_exec(
        'ffmpeg',
        *['-ss', '00:00:01.00',
        '-i', str(path.absolute()),
        '-vframes', '1',
        '-vf', f'scale={s}:{s}:force_original_aspect_ratio=decrease,pad={s}:{s}:(ow-iw)/2:(oh-ih)/2:black',
        '-f', 'singlejpeg', '-'],
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return io.BytesIO(stdout)


async def get_encoded_file_thumbnail(file: FileMetadata, size: int=300) -> str:
    file_path = ROOT_DIR.joinpath(file.name)
    if file.file_type == FileType.AUDIO:
        return ""
    if file.file_type == FileType.IMAGE:
        buff = io.BytesIO()
        img = Image.open(file_path).convert('RGB') # TODO async
        img.thumbnail((size, size))
        img.save(buff, format="JPEG")
    else:
        buff = await get_video_thumbnail(file_path, size)
    return base64.b64encode(buff.getvalue()).decode()

@router.get('/')
async def get_directory_files(repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]) ->  list[FileMetadataDTO]:
    files = await repo.load_all_files()
    res = []
    for file in files:
        thumbnail = await get_encoded_file_thumbnail(file)
        res.append(file_metadata_to_dto(file, thumbnail))
    return res

@router.get("/files-testing")
async def load_sample_files():
    target_dir = '/home/flok3n/minikonrad'

    sample_images = [
        'Screenshot from 2024-06-01 12-27-54.png',
        '352943037_810199457382291_7070402249034345132_n.jpg'
    ]

    sample_videos = [
        '04c0ca69-1da9-440e-906c-e5b097628896.mp4'
    ]

    res = []
    for filename in sample_images:
        buff = io.BytesIO()
        img = Image.open(f'{target_dir}/{filename}').convert('RGB')
        img.thumbnail((300, 300))
        img.save(buff, format="JPEG")
        base64_thumbnail = base64.b64encode(buff.getvalue()).decode()
        res.append({
            "name": filename,
            "thumbnail": base64_thumbnail,
            "type": "image"
        })

    for filename in sample_videos:
        thumbnail = await get_video_thumbnail(f'{target_dir}/{filename}')
        base64_thumbnail = base64.b64encode(thumbnail.getvalue()).decode()
        res.append({
            "name": filename,
            "thumbnail": base64_thumbnail,
            "type": "video"
        })
    
    return res
