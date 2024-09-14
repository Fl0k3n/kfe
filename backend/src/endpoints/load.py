from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_file_repo, get_mapper, get_search_service
from dtos.mappers import Mapper
from dtos.request import FindSimilarItemsRequest, SearchRequest
from dtos.response import LoadAllFilesResponse, SearchResponse, SearchResultDTO
from persistence.file_metadata_repository import FileMetadataRepository
from service.search import SearchService

router = APIRouter(prefix="/load")


@router.get('/')
async def get_directory_files(
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    mapper: Annotated[Mapper, Depends(get_mapper)],
    offset: int = 0,
    limit: int = -1,
) -> LoadAllFilesResponse:
    files = [
        await mapper.file_metadata_to_dto(file)
        for file in await repo.load_files(offset, limit if limit != -1 else None)
    ]
    return LoadAllFilesResponse(files=files, offset=offset, total=await repo.get_number_of_files())

@router.post('/search')
async def search(
    req: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)],
    offset: int = 0,
    limit: int = -1,
) -> SearchResponse:
    search_results, total_items = await search_service.search(req.query, offset, limit if limit != -1 else None)
    results = [await mapper.aggregated_search_result_to_dto(item) for item in search_results]
    return SearchResponse(results=results, offset=offset, total=total_items)

@router.post('/find-similar')
async def find_similar_items(
    req: FindSimilarItemsRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [await mapper.aggregated_search_result_to_dto(item) for item in await search_service.find_similar_items(req.file_id)]
