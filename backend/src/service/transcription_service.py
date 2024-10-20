
from pathlib import Path

from tqdm import tqdm

from features.transcriber import Transcriber
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata
from utils.log import logger


class TranscriptionService:
    def __init__(self, root_dir: Path, transcriber: Transcriber, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.trancriber = transcriber
        self.file_repo = file_repo

    async def init_transcriptions(self, retranscribe_all_auto_trancribed=False):
        if retranscribe_all_auto_trancribed:
            files = await self.file_repo.get_all_audio_files_with_not_manually_fixed_transcript() 
        else:
            files = await self.file_repo.get_all_audio_files_with_not_analyzed_trancription()

        if not files:
            return

        with self.trancriber.run() as engine:
            logger.info(f'generating transcriptions for {len(files)} files...')
            for f in tqdm(files):
                await self._run_transcriber_and_write_results(f, engine)
                await self.file_repo.update_file(f)

    async def transcribe_file(self, file: FileMetadata):
        with self.trancriber.run() as engine:
            await self._run_transcriber_and_write_results(file, engine)

    async def _run_transcriber_and_write_results(self, file: FileMetadata, engine: Transcriber.Engine):
        try:
            file.transcript = await engine.transcribe(self.root_dir.joinpath(file.name))
        except Exception as e:
            logger.error(f'Failed to create transcript for {file.name}', exc_info=e)
        finally:
            file.is_transcript_analyzed = True
