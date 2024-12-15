import asyncio
import re
from pathlib import Path
from typing import Optional

VIDEO_STREAM_FFPROBE_REGEX = re.compile('stream.+?video', re.IGNORECASE)
AUDIO_STREAM_FFPROBE_REGEX = re.compile('stream.+?audio', re.IGNORECASE)

def has_audio_stream(ffprobe_info: str) -> bool:
    return AUDIO_STREAM_FFPROBE_REGEX.search(ffprobe_info) is not None

def has_video_stream(ffprobe_info: str) -> bool:
    return VIDEO_STREAM_FFPROBE_REGEX.search(ffprobe_info) is not None

async def get_ffprobe_stream_info(path: Path) -> Optional[str]:
    try:
        proc = await asyncio.subprocess.create_subprocess_exec(
            'ffprobe', '-i', str(path.absolute()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return None
        full_output = stdout.decode() + " " + stderr.decode()
        return full_output
    except:
        return None
