from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from kfe.dependencies import get_file_repo, get_metadata_editor
from kfe.dtos.request import (UpdateDescriptionRequest, UpdateOCRTextRequest,
                              UpdateScreenshotTypeRequest,
                              UpdateTranscriptRequest)
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileType
from kfe.service.metadata_editor import MetadataEditor

router = APIRouter(prefix="/metadata")

@router.post('/description')
async def update_description(
    req: UpdateDescriptionRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    metadata_editor: Annotated[MetadataEditor, Depends(get_metadata_editor)]
):
    file = await repo.get_file_by_id(req.file_id)
    if file.description != req.description.strip():
        await metadata_editor.update_description(file, req.description.strip())

@router.post('/transcript')
async def update_transcript(
    req: UpdateTranscriptRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    metadata_editor: Annotated[MetadataEditor, Depends(get_metadata_editor)]
):
    file = await repo.get_file_by_id(req.file_id)
    if file.transcript != req.transcript.strip():
        await metadata_editor.update_transcript(file, req.transcript.strip())

@router.post('/ocr')
async def update_ocr_text(
    req: UpdateOCRTextRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    metadata_editor: Annotated[MetadataEditor, Depends(get_metadata_editor)]
):
    file = await repo.get_file_by_id(req.file_id)
    if file.ocr_text != req.ocr_text.strip():
        await metadata_editor.update_ocr_text(file, req.ocr_text.strip())


@router.post('/screenshot')
async def updateScreenshotType(
    req: UpdateScreenshotTypeRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    metadata_editor: Annotated[MetadataEditor, Depends(get_metadata_editor)]
):
    file = await repo.get_file_by_id(req.file_id)
    if file.file_type != FileType.IMAGE:
        raise HTTPException(status_code=400, detail='only images can be marked as screenshots')
    if file.is_screenshot != req.is_screenshot:
        await metadata_editor.update_screenshot_type(file, req.is_screenshot)
