
from pathlib import Path

from tqdm import tqdm

from features.transcriber import Transcriber
from persistence.file_metadata_repository import FileMetadataRepository
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
                try:
                    f.transcript = await engine.transcribe(self.root_dir.joinpath(f.name))
                except Exception as e:
                    logger.error(f'Failed to create transcript for {f.name}', exc_info=e)
                finally:
                    f.is_transcript_analyzed = True
                    await self.file_repo.update_file(f)
