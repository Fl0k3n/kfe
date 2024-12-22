import asyncio
import io
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, AsyncIterator, Awaitable, Callable

import librosa
import torch
from transformers import Pipeline

from kfe.utils.log import logger
from kfe.utils.model_manager import ModelManager, ModelType
from kfe.utils.video_frames_extractor import (get_video_duration_seconds,
                                              seconds_to_ffmpeg_time)


class TranscriberEngine(ABC):
    @abstractmethod
    async def transcribe(self, file_path: Path) -> str:
        pass

class Transcriber(ABC):
    @asynccontextmanager
    @abstractmethod
    async def run(self) -> AsyncGenerator[TranscriberEngine, None]:
        yield


class PipelineBasedTranscriber(Transcriber):
    def __init__(self, model_manager: ModelManager, max_part_length_seconds: float=29., max_num_parts: int=20) -> None:
        self.model_manager = model_manager
        self.max_part_length_seconds = max_part_length_seconds
        self.max_num_parts = max_num_parts
        self.processing_lock = asyncio.Lock()

    @asynccontextmanager
    async def run(self):
        async with self.model_manager.use(ModelType.TRANSCRIBER):
            yield self.Engine(self, lambda: self.model_manager.get_model(ModelType.TRANSCRIBER))

    class Engine(TranscriberEngine):
        def __init__(self, wrapper: 'PipelineBasedTranscriber', lazy_model_provider: Callable[[], Awaitable[tuple[Pipeline, int]]]) -> None:
            self.wrapper = wrapper
            self.model_provider = lazy_model_provider

        async def transcribe(self, file_path: Path) -> str:
            parts = []
            pipeline, sampling_rate = await self.model_provider()
            async for audio_file_bytes in self.wrapper._get_preprocessed_audio_file(file_path, sampling_rate):
                def _transcribe():
                    with torch.no_grad():
                        return pipeline(audio_file_bytes)
                async with self.wrapper.processing_lock:
                    parts.append((await asyncio.get_running_loop().run_in_executor(None,  _transcribe))['text'])
            return ' '.join(parts).strip()

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
            audio_samples, _ = librosa.load(io.BytesIO(stdout), sr=None)
            yield audio_samples
