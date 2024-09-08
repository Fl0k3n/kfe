from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_file_repo, get_thumbnail_manager
from dtos.mappers import file_metadata_to_dto
from dtos.response import FileMetadataDTO
from persistence.file_metadata_repository import FileMetadataRepository
from service.thumbnails import ThumbnailManager

router = APIRouter(prefix="/load")


@router.get('/')
async def get_directory_files(
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    thumbnail_mgr: Annotated[ThumbnailManager, Depends(get_thumbnail_manager)]
) ->  list[FileMetadataDTO]:
    files = await repo.load_all_files()
    res = []
    for file in files:
        thumbnail = await thumbnail_mgr.get_encoded_file_thumbnail(file)
        res.append(file_metadata_to_dto(file, thumbnail))
    return res

