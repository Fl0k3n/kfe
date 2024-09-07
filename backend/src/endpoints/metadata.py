from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_file_repo
from dtos.request import UpdateDescriptionRequest
from persistence.file_metadata_repository import FileMetadataRepository

router = APIRouter(prefix="/metadata")

@router.post('description')
async def update_description(req: UpdateDescriptionRequest, repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]):
    await repo.update_description(req.file_id, req.description)
