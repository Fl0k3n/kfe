import asyncio

from fastapi import APIRouter, BackgroundTasks

from dependencies import ROOT_DIR
from dtos.request import OpenFileRequest

router = APIRouter(prefix="/access")

async def run_file_opener_subprocess(req: OpenFileRequest):
    proc = await asyncio.subprocess.create_subprocess_exec('open', str(ROOT_DIR.joinpath(req.file_name).absolute()))
    print('CREATED')
    ret = await proc.wait()
    print(f'FINISHED: {ret}')
    # subprocess.Popen(['open', '/home/flok3n/minikonrad/352943037_810199457382291_7070402249034345132_n.jpg'])


@router.post("/open")
async def open_file(req: OpenFileRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_file_opener_subprocess, req)
    return {'status': 'ok'}
