
import asyncio
import io
from pathlib import Path

from huggingsound import SpeechRecognitionModel

from utils.log import logger


class Transcriber:
    def __init__(self) -> None:
        self.model = SpeechRecognitionModel("jonatasgrosman/wav2vec2-large-xlsr-53-polish")

    async def transcribe(self, file_path: Path) -> str:
        return self.model.transcribe([await self._get_preprocessed_audio_file(file_path)])[0]['transcription']

    async def _get_preprocessed_audio_file(self, file_path: Path) -> io.BytesIO:
        proc = await asyncio.subprocess.create_subprocess_exec(
            'ffmpeg',
            *['-i', str(file_path.absolute()),
              '-vn', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16384', '-f', 'wav', '-'
            ],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f'ffmpeg returned with {proc.returncode} code for audio transcription preprocessing generation for {file_path.name}')
            logger.debug(f'ffmpeg stderr: {stderr.decode()}')
        return io.BytesIO(stdout)
