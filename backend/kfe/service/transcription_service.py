
from pathlib import Path

from tqdm import tqdm

from kfe.features.transcriber import Transcriber, TranscriberEngine
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata
from kfe.utils.ffprobe import get_ffprobe_stream_info, has_audio_stream
from kfe.utils.init_progress_tracker import InitProgressTracker, InitState
from kfe.utils.log import logger


class TranscriptionService:
    def __init__(self, root_dir: Path, transcriber: Transcriber, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.trancriber = transcriber
        self.file_repo = file_repo

    async def init_transcriptions(self, progress_tracker: InitProgressTracker, retranscribe_all_auto_trancribed=False):
        if retranscribe_all_auto_trancribed:
            files = await self.file_repo.get_all_audio_files_with_not_manually_fixed_transcript() 
        else:
            files = await self.file_repo.get_all_audio_files_with_not_analyzed_trancription()
        progress_tracker.enter_state(InitState.TRANSCIPTION, len(files))

        if not files:
            return

        async with self.trancriber.run() as engine:
            logger.info(f'generating transcriptions for {len(files)} files...')
            for f in tqdm(files, desc='generating transcriptions'):
                await self._run_transcriber_and_write_results(f, engine)
                await self.file_repo.update_file(f)
                progress_tracker.mark_file_processed()

    async def transcribe_file(self, file: FileMetadata):
        async with self.trancriber.run() as engine:
            await self._run_transcriber_and_write_results(file, engine)

    async def _run_transcriber_and_write_results(self, file: FileMetadata, engine: TranscriberEngine):
        file_path = self.root_dir.joinpath(file.name)
        try:
            file.transcript = await engine.transcribe(file_path)
        except Exception as e:
            if has_audio_stream(await get_ffprobe_stream_info(file_path)):
                logger.error(f'Failed to create transcription for {file.name}', exc_info=e)
        finally:
            file.is_transcript_analyzed = True
