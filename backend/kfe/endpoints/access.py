from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from kfe.dependencies import get_file_repo, get_root_dir_path
from kfe.dtos.request import OpenFileRequest
from kfe.dtos.response import SelectDirectoryResponse
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.utils.file_access import (run_directory_picker_and_select_path,
                                   run_file_opener_subprocess,
                                   run_native_file_explorer_subprocess)

router = APIRouter(prefix="/access")

@router.post("/open")
async def open_file(
    req: OpenFileRequest, 
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    root_dir_path: Annotated[Path, Depends(get_root_dir_path)],
    background_tasks: BackgroundTasks
):
    file = await repo.get_file_by_id(req.file_id)
    path = root_dir_path.joinpath(file.name)
    background_tasks.add_task(run_file_opener_subprocess, path)


@router.post("/open-in-directory")
async def open_in_native_explorer(
    req: OpenFileRequest,
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    root_dir_path: Annotated[Path, Depends(get_root_dir_path)],
    background_tasks: BackgroundTasks
):
    file = await repo.get_file_by_id(req.file_id)
    path = root_dir_path.joinpath(file.name)
    background_tasks.add_task(run_native_file_explorer_subprocess, path)


@router.post("/select-directory")
async def select_directory() -> SelectDirectoryResponse:
    selected_path, canceled = await run_directory_picker_and_select_path()
    return SelectDirectoryResponse(
        selected_path=selected_path if selected_path is None else str(selected_path.absolute()),
        canceled=canceled
    ) 
