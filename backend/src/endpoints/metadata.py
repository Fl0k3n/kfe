from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_file_repo, get_metadata_editor
from dtos.request import UpdateDescriptionRequest
from persistence.file_metadata_repository import FileMetadataRepository
from service.metadata_editor import MetadataEditor

router = APIRouter(prefix="/metadata")

@router.post('description')
async def update_description(
    req: UpdateDescriptionRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    metadata_editor: Annotated[MetadataEditor, Depends(get_metadata_editor)]
):
    file = await repo.get_file_by_id(req.file_id)
    if file.description != req.description:
        await metadata_editor.update_description(file, req.description)
