
from pathlib import Path

from features.transcriber import Transcriber
from persistence.file_metadata_repository import FileMetadataRepository
from utils.log import logger


class TranscriptionService:
    def __init__(self, root_dir: Path, transcriber: Transcriber, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.trancriber = transcriber
        self.file_repo = file_repo

    async def init_transcriptions(self):
        for f in await self.file_repo.get_all_audio_files_with_not_analyzed_trancription():
            try:
                f.transcript = await self.trancriber.transcribe(self.root_dir.joinpath(f.name))
                print()
            except Exception as e:
                logger.error(f'Failed to create transcript for {f.name}', exc_info=e)
            finally:
                f.is_transcript_analyzed = True
                await self.file_repo.update_file(f)
