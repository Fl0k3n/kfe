
import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from kfe.dependencies import get_directory_context_holder, get_directory_repo
from kfe.directory_context import DirectoryContextHolder
from kfe.dtos.request import (RegisterDirectoryRequest,
                              UnregisterDirectoryRequest)
from kfe.dtos.response import RegisteredDirectoryDTO
from kfe.persistence.directory_repository import DirectoryRepository
from kfe.persistence.model import RegisteredDirectory
from kfe.utils.constants import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/directory")

@router.get('/')
async def list_registered_directories(
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
) -> list[RegisteredDirectoryDTO]:
    res = []
    for d in await directory_repo.get_all():
        if init_progress := ctx_holder.get_init_progress(d.name):
            res.append(RegisteredDirectoryDTO(
                name=d.name,
                ready=ctx_holder.has_context(d.name),
                failed=ctx_holder.has_init_failed(d.name),
                init_progress_description=init_progress[0],
                init_progress=init_progress[1],
            ))
        else:
            res.append(RegisteredDirectoryDTO(
                name=d.name,
                ready=ctx_holder.has_context(d.name),
                failed=ctx_holder.has_init_failed(d.name),
            ))
    return res

@router.post('/')
async def register_directory(
    req: RegisterDirectoryRequest,
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
) -> RegisteredDirectoryDTO:
    if req.primary_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f'primary language must be one of {SUPPORTED_LANGUAGES}')
    directory = RegisteredDirectory(
        name=req.name,
        fs_path=req.path,
        primary_language=req.primary_language,
    )
    if not directory.path.exists():
        raise HTTPException(status_code=404, detail='path does not exist')
    await directory_repo.add(directory)
    task = asyncio.create_task(ctx_holder.register_directory(directory.name, directory.path, directory.primary_language))
    ctx_holder.directory_init_background_tasks.add(task)
    task.add_done_callback(ctx_holder.directory_init_background_tasks.discard)
    return RegisteredDirectoryDTO(name=directory.name, ready=False, failed=False)

@router.delete('/')
async def unregister_directory(
    req: UnregisterDirectoryRequest,
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
    background_tasks: BackgroundTasks
):
    if not ctx_holder.is_initialized():
        raise HTTPException(status_code=503, detail='context of directories is not initialized yet, unregistering forbidden')
    directory = await directory_repo.get_by_name(req.name)
    if directory is None:
        raise HTTPException(status_code=404, detail='directory is not registered')
    await directory_repo.remove(directory)
    background_tasks.add_task(ctx_holder.unregister_directory, directory.name)
