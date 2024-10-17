import io
import subprocess as sp
from pathlib import Path

from PIL import Image


def _seconds_to_ffmpeg_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:05.2f}"

def get_video_duration_seconds(path: Path) -> float:
    duration_proc = sp.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path.absolute())],
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )
    if duration_proc.returncode != 0:
        raise ValueError(f'failed to get video duration for video: {path}\nerror: {duration_proc.stderr.decode()}')
    return float(duration_proc.stdout.decode())

def get_video_frame_at_offset(path: Path, seconds: float) -> Image.Image:
    ss = _seconds_to_ffmpeg_time(seconds)
    proc = sp.run(
        ['ffmpeg',
        '-ss', ss,
        '-i', path,
        '-vframes', '1',
        '-f', 'singlejpeg', '-'],
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )

    if proc.returncode != 0:
        raise  ValueError(f'failed to get video frame at offset: {seconds}, path: {path}\nerror: {proc.stderr.decode()}')
    return Image.open(io.BytesIO(proc.stdout)).convert('RGB')
