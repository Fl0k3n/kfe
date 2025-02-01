from pathlib import Path

from tqdm import tqdm

from kfe.features.vision_lm_engine import VisionLMEngine
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileType
from kfe.utils.init_progress_tracker import InitProgressTracker, InitState
from kfe.utils.log import logger


class VisionLMService:
    def __init__(self, root_dir: Path, vision_lm_engine: VisionLMEngine, file_repo: FileMetadataRepository) -> None:
        self.root_dir = root_dir
        self.vision_lm_engine = vision_lm_engine
        self.file_repo = file_repo

    async def init_vision_lm_descriptions(self, progress_tracker: InitProgressTracker, regenerate_all: bool=False):
        if regenerate_all:
            files = await self.file_repo.get_all_files_with_type(FileType.IMAGE)
        else:
            files = await self.file_repo.get_all_images_with_no_llm_description()
        progress_tracker.enter_state(InitState.LLM_DESCRIPTION, len(files))

        if not files:
            return

        async with self.vision_lm_engine.run() as engine:
            logger.info(f'generating LLM descriptions for {len(files)} files...')
            for f in tqdm(files, desc='generating LLM descriptions'):
                try:
                    description = await engine.generate_description(self.root_dir.joinpath(f.name))
                    f.llm_description = description
                except Exception as e:
                    logger.error(f'Failed to create LLM description for {f.name}', exc_info=e)
                f.is_llm_description_analyzed = True
                await self.file_repo.update_file(f)
                progress_tracker.mark_file_processed()
