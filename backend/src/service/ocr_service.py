from pathlib import Path

from features.ocr_engine import OCREngine
from persistence.file_metadata_repository import FileMetadataRepository


class OCRService:
    def __init__(self, root_dir: Path, file_repo: FileMetadataRepository, ocr_engine: OCREngine) -> None:
        self.root_dir = root_dir
        self.file_repo = file_repo
        self.ocr_engine = ocr_engine

    async def init_ocrs(self):
        files = await self.file_repo.get_all_images_with_not_analyzed_ocr()
        for f in files:
            text, is_screenshot = self.ocr_engine.run_ocr(str(self.root_dir.joinpath(f.name).absolute()))
            f.is_ocr_analyzed = True
            f.is_screenshot = is_screenshot
            if is_screenshot:
                f.ocr_text = text
                if f.description == '':
                    f.description = text
            await self.file_repo.update_file(f)
