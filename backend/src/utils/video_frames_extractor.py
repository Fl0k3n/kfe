import asyncio
import io
from pathlib import Path

from PIL import Image


def seconds_to_ffmpeg_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:05.2f}"

async def get_video_duration_seconds(path: Path) -> float:
    proc = await asyncio.subprocess.create_subprocess_exec(
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path.absolute()),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise ValueError(f'failed to get video duration for video: {path}\nerror: {stderr.decode()}')
    return float(stdout.decode())

async def get_video_frame_at_offset(path: Path, seconds: float) -> Image.Image:
    ss_offset = seconds_to_ffmpeg_time(seconds)
    proc = await asyncio.subprocess.create_subprocess_exec(
        'ffmpeg',
        '-ss', ss_offset,
        '-i', str(path.absolute()),
        '-vframes', '1',
        '-f', 'mjpeg', '-',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise  ValueError(f'failed to get video frame at offset: {seconds}, path: {path}\nerror: {stderr.decode()}')
    return Image.open(io.BytesIO(stdout)).convert('RGB')
