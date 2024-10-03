
import asyncio
import io
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from huggingsound import SpeechRecognitionModel

from utils.log import logger
from utils.model_manager import ModelManager, ModelType


class Transcriber:
    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    @contextmanager
    def run(self):
        with self.model_manager.use(ModelType.TRANSCRIBER):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TRANSCRIBER))

    class Engine:
        def __init__(self, wrapper: 'Transcriber', lazy_model_provider: Callable[[], SpeechRecognitionModel]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def transcribe(self, file_path: Path) -> str:
            return self.model_provider().transcribe([await self._get_preprocessed_audio_file(file_path)])[0]['transcription']

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
