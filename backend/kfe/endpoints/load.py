from typing import Annotated

from fastapi import APIRouter, Depends

from kfe.dependencies import get_file_repo, get_mapper, get_search_service
from kfe.dtos.mappers import Mapper
from kfe.dtos.request import (FindSimilarImagesToUploadedImageRequest,
                              FindSimilarItemsRequest,
                              GetOffsetOfFileInLoadResultsRequest,
                              SearchRequest)
from kfe.dtos.response import (GetOffsetOfFileInLoadResultsResponse,
                               LoadAllFilesResponse, SearchResponse,
                               SearchResultDTO)
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.service.search import SearchService

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

@router.post('/find-with-similar-description')
async def find_items_with_similar_descriptions(
    req: FindSimilarItemsRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [await mapper.aggregated_search_result_to_dto(item) for item in await search_service.find_items_with_similar_descriptions(req.file_id)]

@router.post('/find-with-similar-metadata')
async def find_items_with_similar_metadata(
    req: FindSimilarItemsRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [await mapper.aggregated_search_result_to_dto(item) for item in await search_service.find_items_with_similar_metadata(req.file_id)]

@router.post('/find-visually-similar-images')
async def find_visually_similar_images(
    req: FindSimilarItemsRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [await mapper.aggregated_search_result_to_dto(item) for item in await search_service.find_visually_similar_images(req.file_id)]

@router.post('/find-visually-similar-videos')
async def find_visually_similar_videos(
    req: FindSimilarItemsRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [await mapper.aggregated_search_result_to_dto(item) for item in await search_service.find_visually_similar_videos(req.file_id)]

@router.post('/find-similar-to-uploaded-image')
async def find_visually_similar_images_to_uploaded_image(
    req: FindSimilarImagesToUploadedImageRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    mapper: Annotated[Mapper, Depends(get_mapper)]
) -> list[SearchResultDTO]:
    return [
        await mapper.aggregated_search_result_to_dto(item)
        for item in await search_service.find_visually_similar_images_to_image(req.image_data_base64)
    ] 

@router.post('/get-offset-in-load-results')
async def get_file_offset_in_load_results(
    req: GetOffsetOfFileInLoadResultsRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]
) -> GetOffsetOfFileInLoadResultsResponse:
    return GetOffsetOfFileInLoadResultsResponse(idx=await repo.get_file_offset_within_sorted_results(req.file_id))
