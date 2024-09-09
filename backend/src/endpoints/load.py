from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import (get_file_repo, get_search_service,
                          get_thumbnail_manager)
from dtos.mappers import file_metadata_to_dto
from dtos.request import SearchRequest
from dtos.response import FileMetadataDTO
from persistence.file_metadata_repository import FileMetadataRepository
from service.search import SearchService
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


@router.post('/search')
async def search(
    req: SearchRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    search_service: Annotated[SearchService, Depends(get_search_service)],
    thumbnail_mgr: Annotated[ThumbnailManager, Depends(get_thumbnail_manager)]
) -> list[FileMetadataDTO]:
    items = search_service.search(req.query)
    files = await repo.load_all_files()
    file_by_id = {int(f.id): f for f in files}
    res = []
    for item in items:
        file = file_by_id[item.item_idx]
        thumbnail = await thumbnail_mgr.get_encoded_file_thumbnail(file)
        res.append(file_metadata_to_dto(file, thumbnail))
    return res
