import asyncio
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from dependencies import get_file_repo, get_root_dir_path
from dtos.request import OpenFileRequest
from persistence.file_metadata_repository import FileMetadataRepository

router = APIRouter(prefix="/access")

async def run_file_opener_subprocess(path: Path):
    proc = await asyncio.subprocess.create_subprocess_exec(
        'open', path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

async def run_native_file_explorer_subprocess(path: Path):
    if sys.platform == 'darwin':
        command = ['open' '-r', path]
    else:
        command = ['nautilus', '--select', path]
    proc = await asyncio.subprocess.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
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
    return {'status': 'ok'}
