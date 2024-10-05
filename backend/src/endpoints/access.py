import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from dependencies import ROOT_DIR, get_file_repo
from dtos.request import OpenFileRequest
from persistence.file_metadata_repository import FileMetadataRepository

router = APIRouter(prefix="/access")

async def run_file_opener_subprocess(path: Path):
    proc = await asyncio.subprocess.create_subprocess_exec('open', path)
    print('CREATED')
    ret = await proc.wait()
    print(f'FINISHED: {ret}')


@router.post("/open")
async def open_file(
    req: OpenFileRequest, 
    repo: Annotated[FileMetadataRepository, Depends(get_file_repo)],
    background_tasks: BackgroundTasks
):
    file = await repo.get_file_by_id(req.file_id)
    path = ROOT_DIR.joinpath(file.name)
    background_tasks.add_task(run_file_opener_subprocess, path)
    return {'status': 'ok'}
