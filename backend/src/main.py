import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from dependencies import init, teardown
from endpoints.access import router as access_router
from endpoints.directories import router as directories_router
from endpoints.events import router as events_router
from endpoints.load import router as load_router
from endpoints.metadata import router as metadata_router
from utils.constants import GENERATE_OPENAPI_SCHEMA_ON_STARTUP_ENV
from utils.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init()
    yield
    await teardown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware('http')
async def localhost_firewall(request: Request, call_next):
    ip = str(request.client.host)
    if ip not in ('0.0.0.0', '127.0.0.1', '00:00:00:00:00:00', '::', '00:00:00:00:00:01', '::1'):
        return JSONResponse(status_code=403, content={'message': 'access forbidden'})
    return await call_next(request)

app.include_router(load_router, tags=['load'])
app.include_router(access_router, tags=['access'])
app.include_router(metadata_router, tags=['metadata'])
app.include_router(events_router, tags=['events'])
app.include_router(directories_router, tags=['directories'])

frontend_build_path = Path(__file__).resolve().parent.parent.parent.joinpath('frontend').joinpath('build')
try:
    app.mount('/', StaticFiles(directory=frontend_build_path, html=True), name='static')
except Exception:
    logger.error(f'failed to access frontend files, run "npm build" in frontend directory and make sure results are present in {frontend_build_path}')
    raise 

if __name__ == "__main__":
    if os.getenv(GENERATE_OPENAPI_SCHEMA_ON_STARTUP_ENV, 'true') == 'true':
        with open(Path(__file__).resolve().parent.joinpath('schema.json'), 'w') as f:
            json.dump(app.openapi(), f)
    uvicorn.run(app, host="0.0.0.0", port=8000)
