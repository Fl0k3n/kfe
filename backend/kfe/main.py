import json
import logging
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import click
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from kfe.utils.constants import (DEVICE_ENV, LOG_LEVEL_ENV,
                                 PRELOAD_THUMBNAILS_ENV,
                                 REGENERATE_LLM_DESCRIPTIONS_ENV,
                                 RETRANSCRIBE_AUTO_TRANSCRIBED_ENV,
                                 TRANSCRIPTION_MODEL_ENV)


@click.command()
@click.option('--host', default='127.0.0.1', show_default=True, help='Address on which application should be available.')
@click.option('--port', default=8000, type=int, show_default=True, help='Port on which application should be available.')
@click.option('--cpu', default=False, is_flag=True, show_default=True, help='Use CPU for models even if GPU is available.')
@click.option('--transcription-model', default=None, help='Choose transcription model. By default openai/whisper-large-v3 will be used if you have CUDA GPU or Apple silicon, otherwise openai/whisper-base will be used. See https://huggingface.co/openai/whisper-large-v3-turbo#model-details for alternatives, parameter that you pass should be "openai/whisper-<variant>".')
@click.option('--retranscribe-auto-transcribed', default=False, is_flag=True, show_default=True, help='Whether transcriptions should be regenerated on startup. Transcriptions that you edited manually using GUI will not be affected. This can be useful if you changed the model.')
@click.option('--regenerate-llm-descriptions', default=False, is_flag=True, show_default=True, help='Whether LLM descriptions should be regenerated on startup. This can be useful if you changed the model or the prompt.')
@click.option('--no-preload-thumbnails', default=False, is_flag=True, show_default=True, help='Do not load all file thumbnails to memory on startup. Application will use less memory but queries will be slower.')
@click.option('--no-firewall', default=False, is_flag=True, show_default=True, help='Do not block connections from external addresses (other than localhost and 0.0.0.0).')
@click.option('--log-level', default='INFO', show_default=True, type=click.Choice(list(logging._nameToLevel.keys())))
def main(host: str, port: int, cpu: bool, transcription_model: Optional[str], retranscribe_auto_transcribed: bool, 
         regenerate_llm_descriptions: bool, no_preload_thumbnails: bool, no_firewall: bool, log_level: str):
    print('starting kfe server...')

    os.environ[LOG_LEVEL_ENV] = log_level
    if cpu:
        os.environ[DEVICE_ENV] = 'cpu'
    if transcription_model is not None:
        os.environ[TRANSCRIPTION_MODEL_ENV] = transcription_model
    if retranscribe_auto_transcribed:
        os.environ[RETRANSCRIBE_AUTO_TRANSCRIBED_ENV] = 'true'
    if regenerate_llm_descriptions:
        os.environ[REGENERATE_LLM_DESCRIPTIONS_ENV] = 'true'
    if no_preload_thumbnails:
        os.environ[PRELOAD_THUMBNAILS_ENV] = 'false'

    from kfe.dependencies import init, on_http_request_middleware, teardown
    from kfe.endpoints.access import router as access_router
    from kfe.endpoints.directories import router as directories_router
    from kfe.endpoints.files import router as files_router
    from kfe.endpoints.metadata import router as metadata_router
    from kfe.utils.constants import GENERATE_OPENAPI_SCHEMA_ON_STARTUP_ENV
    from kfe.utils.log import logger

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init()
        yield
        await teardown()

    app = FastAPI(lifespan=lifespan)

    if not no_firewall:
        @app.middleware('http')
        async def localhost_firewall(request: Request, call_next):
            ip = str(request.client.host)
            if ip not in ('0.0.0.0', '127.0.0.1', '00:00:00:00:00:00', '::', '00:00:00:00:00:01', '::1'):
                return JSONResponse(status_code=403, content={'message': 'access forbidden'})
            return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware('http')
    async def app_dynamic_middleware(request: Request, call_next):
        return await on_http_request_middleware(request, call_next)

    app.include_router(files_router, tags=['files'])
    app.include_router(access_router, tags=['access'])
    app.include_router(metadata_router, tags=['metadata'])
    app.include_router(directories_router, tags=['directories'])

    frontend_build_path = Path(__file__).parent.joinpath('resources').joinpath('frontend_build')
    try:
        app.mount('/', StaticFiles(directory=frontend_build_path, html=True), name='static')
    except Exception:
        logger.error(f'failed to access frontend files, run "npm build" in frontend directory and make sure results are present in {frontend_build_path}')
        raise

    if os.getenv(GENERATE_OPENAPI_SCHEMA_ON_STARTUP_ENV, 'true') == 'true':
        try:
            with open(Path(__file__).resolve().parent.joinpath('schema.json'), 'w') as f:
                json.dump(app.openapi(), f)
        except Exception as e:
            logger.error(f'Failed to generate openapi spec', exc_info=e)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                logger.info(f'Port {port} is taken, selecting random port automatically, use kfe --port to overwrite.')
                port = 0
            else:
                logger.info(f'starting application on http://{host}:{port}')
    except:
        pass

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
