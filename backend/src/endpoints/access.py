import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from dependencies import get_file_repo, get_root_dir_path
from dtos.request import OpenFileRequest
from persistence.file_metadata_repository import FileMetadataRepository

router = APIRouter(prefix="/access")

async def run_file_opener_subprocess(path: Path):
    proc = await asyncio.subprocess.create_subprocess_exec('open', path)
    await proc.wait()

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
    return {'status': 'ok'}


@router.post("/open-directory")
async def open_native_explorer(
    root_dir_path: Annotated[Path, Depends(get_root_dir_path)],
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(run_file_opener_subprocess, root_dir_path)
    return {'status': 'ok'}
