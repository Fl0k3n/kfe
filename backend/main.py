import asyncio
import base64
import io
import os
import subprocess

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies to be sent with the requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


# paginated file endpoints, should deliver files (with thumnails) in some range, ordered by some metric
@app.get("/files")
async def get_files():
    return [
        {
            "name": "some file",
            "metadata": "TODO"
        }
    ]


# here we accept a search query and return K files
@app.post("/search")
async def search():
    return await get_files()


# here we accept a file and return a list of similar files
@app.post("/similarity")
async def find_similar_files():
    return await get_files()


class OpenFileRequest(BaseModel):
    file_name: str


async def run_file_opener_subprocess(req: OpenFileRequest):
    path = f'/home/flok3n/minikonrad/{req.file_name}'
    proc = await asyncio.subprocess.create_subprocess_exec('open', path)
    print('CREATED')
    ret = await proc.wait()
    print(f'FINISHED: {ret}')
    # subprocess.Popen(['open', '/home/flok3n/minikonrad/352943037_810199457382291_7070402249034345132_n.jpg'])

async def get_video_thumbnail(path: str) -> io.BytesIO:
    proc = await asyncio.subprocess.create_subprocess_exec(
        'ffmpeg',
        *['-ss', '00:00:01.00',
        '-i', path,
        '-vframes', '1',
        '-vf', 'scale=320:320:force_original_aspect_ratio=decrease,pad=320:320:(ow-iw)/2:(oh-ih)/2:black',
        '-f', 'singlejpeg', '-'],
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return io.BytesIO(stdout)

@app.post("/open")
async def open_file(req: OpenFileRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_file_opener_subprocess, req)
    return {'status': 'ok'}


@app.get("/files-testing")
async def load_sample_files():
    target_dir = '/home/flok3n/minikonrad'

    sample_images = [
        'Screenshot from 2024-06-01 12-27-54.png',
        '352943037_810199457382291_7070402249034345132_n.jpg'
    ]

    sample_videos = [
        '04c0ca69-1da9-440e-906c-e5b097628896.mp4'
    ]

    res = []
    for filename in sample_images:
        buff = io.BytesIO()
        img = Image.open(f'{target_dir}/{filename}').convert('RGB')
        img.thumbnail((300, 300))
        img.save(buff, format="JPEG")
        base64_thumbnail = base64.b64encode(buff.getvalue()).decode()
        res.append({
            "name": filename,
            "thumbnail": base64_thumbnail,
            "type": "image"
        })

    for filename in sample_videos:
        thumbnail = await get_video_thumbnail(f'{target_dir}/{filename}')
        base64_thumbnail = base64.b64encode(thumbnail.getvalue()).decode()
        res.append({
            "name": filename,
            "thumbnail": base64_thumbnail,
            "type": "video"
        })

    
    return res

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
