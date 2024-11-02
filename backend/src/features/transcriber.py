
import asyncio
import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Awaitable, Callable

from huggingsound import Decoder, SpeechRecognitionModel

from utils.log import logger
from utils.model_manager import ModelManager, ModelType


class Transcriber:
    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.TRANSCRIBER):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TRANSCRIBER))

    class Engine:
        def __init__(self, wrapper: 'Transcriber', lazy_model_provider: Callable[[], Awaitable[tuple[SpeechRecognitionModel, Decoder]]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def transcribe(self, file_path: Path) -> str:
            audio_file_bytes = await self.wrapper._get_preprocessed_audio_file(file_path)
            model, decoder = await self.model_provider()
            def _trascribe():
                return model.transcribe([audio_file_bytes], decoder=decoder)[0]['transcription']
            return await asyncio.get_running_loop().run_in_executor(None,  _trascribe)

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
