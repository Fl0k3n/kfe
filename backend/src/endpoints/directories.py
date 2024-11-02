
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from dependencies import get_directory_context_holder, get_directory_repo
from directory_context import DirectoryContextHolder
from dtos.request import RegisterDirectoryRequest, UnregisterDirectoryRequest
from dtos.response import RegisteredDirectoryDTO
from persistence.directory_repository import DirectoryRepository
from persistence.model import RegisteredDirectory

router = APIRouter(prefix="/directory")

@router.get('/')
async def list_registered_directories(
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
) -> list[RegisteredDirectoryDTO]:
    return [
        RegisteredDirectoryDTO(name=d.name, ready=ctx_holder.has_context(d.name), failed=ctx_holder.has_init_failed(d.name))
        for d in await directory_repo.get_all()
    ]

@router.post('/')
async def register_directory(
    req: RegisterDirectoryRequest,
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
    background_tasks: BackgroundTasks
) -> RegisteredDirectoryDTO:
    if not req.languages:
        raise HTTPException(status_code=400, detail=f'must specify at least one expected language')
    directory = RegisteredDirectory(
        name=req.name,
        fs_path=req.path,
        comma_separated_languages=','.join(req.languages)
    )
    if not directory.path.exists():
        raise HTTPException(status_code=404, detail='path does not exist')
    await directory_repo.add(directory)
    background_tasks.add_task(ctx_holder.register_directory, directory.name, directory.path, directory.languages)
    return RegisteredDirectoryDTO(name=directory.name, ready=False, failed=False)

@router.delete('/')
async def unregister_directory(
    req: UnregisterDirectoryRequest,
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    ctx_holder: Annotated[DirectoryContextHolder, Depends(get_directory_context_holder)],
    background_tasks: BackgroundTasks   
):
    directory = await directory_repo.get_by_name(req.name)
    if directory is None:
        raise HTTPException(status_code=404, detail='directory is not registered')
    await directory_repo.remove(directory)
    background_tasks.add_task(ctx_holder.unregister_directory, directory.name)
