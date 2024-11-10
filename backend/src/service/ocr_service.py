from pathlib import Path

from tqdm import tqdm

from features.ocr_engine import OCREngine
from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata


class OCRService:
    def __init__(self, root_dir: Path, file_repo: FileMetadataRepository, ocr_engine: OCREngine) -> None:
        self.root_dir = root_dir
        self.file_repo = file_repo
        self.ocr_engine = ocr_engine

    async def init_ocrs(self):
        files = await self.file_repo.get_all_images_with_not_analyzed_ocr()
        async with self.ocr_engine.run() as engine:
            for f in tqdm(files, desc='generating OCR texts'):
                await self._run_ocr_and_write_results(f, engine)
                await self.file_repo.update_file(f)

    async def perform_ocr(self, file: FileMetadata):
        async with self.ocr_engine.run() as engine:
            await self._run_ocr_and_write_results(file, engine)

    async def _run_ocr_and_write_results(self, file: FileMetadata, engine: OCREngine.Engine):
        text, is_screenshot = await engine.run_ocr(self.root_dir.joinpath(file.name))
        file.is_ocr_analyzed = True
        file.is_screenshot = is_screenshot
        if is_screenshot:
            file.ocr_text = text
            if file.description == '':
                file.description = text
