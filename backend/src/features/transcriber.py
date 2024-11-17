
import asyncio
import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, Optional

from huggingsound.decoder import Decoder
from huggingsound.model import SpeechRecognitionModel
from utils.log import logger
from utils.model_manager import ModelManager, ModelType
from utils.video_frames_extractor import (get_video_duration_seconds,
                                          seconds_to_ffmpeg_time)


class Transcriber:
    def __init__(self, model_manager: ModelManager, max_part_length_seconds: float=60., max_num_parts: int= 15) -> None:
        self.model_manager = model_manager
        self.max_part_length_seconds = max_part_length_seconds
        self.max_num_parts = max_num_parts

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.TRANSCRIBER):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TRANSCRIBER))

    class Engine:
        def __init__(self, wrapper: 'Transcriber', lazy_model_provider: Callable[[], Awaitable[tuple[SpeechRecognitionModel, Optional[Decoder]]]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def transcribe(self, file_path: Path) -> str:
            parts = []
            model, decoder = await self.model_provider()
            async for audio_file_bytes in self.wrapper._get_preprocessed_audio_file(file_path, model.get_sampling_rate()):
                def _trascribe():
                    return model.transcribe([audio_file_bytes], decoder=decoder)[0]['transcription']
                part = await asyncio.get_running_loop().run_in_executor(None,  _trascribe)
                parts.append(part)
            return ' '.join(parts)

    async def _get_preprocessed_audio_file(self, file_path: Path, sampling_rate: int) -> AsyncIterator[io.BytesIO]:
        duration = await get_video_duration_seconds(file_path)
        for i in range(min(int(duration) // int(self.max_part_length_seconds) + 1, self.max_num_parts)):
            proc = await asyncio.subprocess.create_subprocess_exec(
                'ffmpeg',
                '-i', str(file_path.absolute()),
                '-ss', seconds_to_ffmpeg_time(i * self.max_part_length_seconds),
                '-to', seconds_to_ffmpeg_time(min(duration, (i + 1) * self.max_part_length_seconds)),
                '-vn', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', str(sampling_rate), '-f', 'wav', '-',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f'ffmpeg returned with {proc.returncode} code for audio transcription preprocessing generation for {file_path.name}')
                logger.debug(f'ffmpeg stderr: {stderr.decode()}')
            yield io.BytesIO(stdout)
