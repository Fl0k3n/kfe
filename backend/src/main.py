import json
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dependencies import init, teardown
from endpoints.access import router as access_router
from endpoints.load import router as load_router
from endpoints.metadata import router as metadata_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init(should_dump_descriptions=False, should_restore_descriptions=False)
    yield
    await teardown()

app = FastAPI(lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies to be sent with the requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
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


if __name__ == "__main__":
    with open(Path(__file__).resolve().parent.joinpath('schema.json'), 'w') as f:
       json.dump(app.openapi(), f)
    uvicorn.run(app, host="0.0.0.0", port=8000)
