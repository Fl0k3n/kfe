import asyncio
import os
from pathlib import Path
from typing import Annotated, AsyncGenerator

import easyocr
import spacy
import spacy.cli
import spacy.cli.download
import torch
from fastapi import Depends, Header, HTTPException
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import (AutoModelForSpeechSeq2Seq, AutoProcessor, CLIPModel,
                          CLIPProcessor, Pipeline, pipeline)

from kfe.directory_context import DirectoryContext, DirectoryContextHolder
from kfe.dtos.mappers import Mapper
from kfe.features.text_embedding_engine import TextModelWithConfig
from kfe.persistence.db import Database
from kfe.persistence.directory_repository import DirectoryRepository
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.service.metadata_editor import MetadataEditor
from kfe.service.search import SearchService
from kfe.service.thumbnails import ThumbnailManager
from kfe.utils.constants import (DEVICE_ENV, DIRECTORY_NAME_HEADER,
                                 LOG_SQL_ENV, TRANSCRIPTION_MODEL_ENV,
                                 Language)
from kfe.utils.log import logger
from kfe.utils.model_cache import try_loading_cached_or_download
from kfe.utils.model_manager import (ModelManager, ModelType,
                                     SecondaryModelManager)
from kfe.utils.paths import CONFIG_DIR
from kfe.utils.platform import is_apple_silicon, is_windows

REFRESH_PERIOD_SECONDS = 3600 * 24.

device = torch.device('cuda' if torch.cuda.is_available() and os.getenv(DEVICE_ENV, 'cuda') == 'cuda' else 'cpu')
if os.getenv(DEVICE_ENV) != 'cpu' and not is_apple_silicon() and not torch.cuda.is_available():
    logger.warning('cuda unavailable')

def get_ocr_model(language: Language) -> easyocr.Reader:
    return easyocr.Reader(
        ['en'] if language == 'en' else [language, 'en'],
        gpu=str(device) == 'cuda'
    )

def get_lemmatizer_model(language: Language, download_on_loading_fail=True) -> spacy.language.Language:
    model = 'pl_core_news_lg' if language == 'pl' else 'en_core_web_trf'
    try:
        return spacy.load(model, disable=['morphologizer', 'parser', 'senter', 'ner'])
    except Exception as e:
        if download_on_loading_fail:
            logger.error(f'Failed to use lemmatizer {model}, attempting download...', exc_info=e)
            spacy.cli.download(model)
            return get_lemmatizer_model(language, download_on_loading_fail=False)
        else:
            raise

def get_text_embedding_model(language: Language):
    return TextModelWithConfig(
        model=try_loading_cached_or_download(
            'ipipan/silver-retriever-base-v1.1' if language == 'pl' else 'sentence-transformers/all-mpnet-base-v2',
            lambda x: SentenceTransformer(x.model_path, cache_folder=x.cache_dir, local_files_only=x.local_files_only)
        ).to(device),
        query_prefix='Pytanie: ' if language == 'pl' else '',
        passage_prefix='</s>' if language == 'pl' else ''
    )

def get_clip_model() -> tuple[CLIPProcessor, CLIPModel]:
    clip_processor = try_loading_cached_or_download(
        "openai/clip-vit-base-patch32",
        lambda x: CLIPProcessor.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only),
        cache_dir_must_have_file='preprocessor_config.json'
    )
    clip_model = try_loading_cached_or_download(
        "openai/clip-vit-base-patch32",
        lambda x: CLIPModel.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only),
        cache_dir_must_have_file='pytorch_model.bin'
    ).to(device)
    return clip_processor, clip_model

def get_transcription_model() -> tuple[Pipeline, int]:
    torch_dtype = torch.float16 if str(device) == 'cuda' else torch.float32
    model_id = os.getenv(TRANSCRIPTION_MODEL_ENV)
    if model_id is None:
        if str(device) == 'cuda' or is_apple_silicon():
            model_id = "openai/whisper-large-v3"
        else:
            # see https://huggingface.co/openai/whisper-large-v3-turbo#model-details for alternatives
            model_id = "openai/whisper-base"
    # TODO flash attention
    model = try_loading_cached_or_download(
        model_id,
        lambda x: AutoModelForSpeechSeq2Seq.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only,
            torch_dtype=torch_dtype, use_safetensors=True, low_cpu_mem_usage=True),
        cache_dir_must_have_file='model.safetensors'
    ).to(device)
    processor = try_loading_cached_or_download(
        model_id,
        lambda x: AutoProcessor.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only),
        cache_dir_must_have_file='generation_config.json'
    )
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )
    sampling_rate = 16_000 # whisper was trained on that
    return pipe, sampling_rate

pl_model_manager = ModelManager(model_providers={
    ModelType.OCR: lambda: get_ocr_model('pl'),
    ModelType.TRANSCRIBER: get_transcription_model,
    ModelType.TEXT_EMBEDDING: lambda: get_text_embedding_model('pl'),
    ModelType.CLIP: get_clip_model,
    ModelType.LEMMATIZER: lambda: get_lemmatizer_model('pl'),
})

en_model_manager = SecondaryModelManager(primary=pl_model_manager, owned_model_providers={
    ModelType.OCR: lambda: get_ocr_model('en'),
    ModelType.TEXT_EMBEDDING: lambda: get_text_embedding_model('en'),
    ModelType.LEMMATIZER: lambda: get_lemmatizer_model('en'),
})

model_managers = {
    'pl': pl_model_manager,
    'en': en_model_manager,
}

directory_context_holder = DirectoryContextHolder(
    model_managers=model_managers,
    device=device
)

app_db = Database(CONFIG_DIR, log_sql=os.getenv(LOG_SQL_ENV, 'false') == 'true')

async def init():
    if 'TOKENIZERS_PARALLELISM' not in os.environ:
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if is_windows() and 'HF_HUB_DISABLE_SYMLINKS_WARNING' not in os.environ:
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = "true"
    logger.info(f'initializing shared app db in directory: {CONFIG_DIR}')
    await app_db.init_db()
    async def init_directories_in_background():
        async with app_db.session() as sess:
            registered_directories = await DirectoryRepository(sess).get_all()
        for directory in registered_directories:
            logger.info(f'initializing registered directory: {directory.name}, from: {directory.path}')
            try:
                await directory_context_holder.register_directory(directory.name, directory.path, directory.primary_language)
            except Exception as e:
                logger.error(f'Failed to initialize directory: {directory.name}', exc_info=e)
        directory_context_holder.set_initialized()
        asyncio.create_task(schedule_periodic_refresh())
    asyncio.create_task(init_directories_in_background())


async def schedule_periodic_refresh():
    # since directory content change watching is not guaranteed to capture every change
    # we schedule reloads to ensure consistency if app is not restarted for longer time
    await asyncio.sleep(REFRESH_PERIOD_SECONDS)
    async with app_db.session() as sess:
        registered_directories = await DirectoryRepository(sess).get_all()
    for directory in registered_directories:
        try:
            await directory_context_holder.unregister_directory(directory.name)
            await directory_context_holder.register_directory(directory.name, directory.path, directory.primary_language)
        except Exception as e:
            logger.error(f'Failed to refresh directory: {directory.name}', exc_info=e)
    asyncio.create_task(schedule_periodic_refresh())

def get_model_managers() -> dict[Language, ModelManager]:
    return model_managers

def get_directory_context_holder() -> DirectoryContextHolder:
    return directory_context_holder

def get_directory_context(x_directory: Annotated[str, Header()]) -> DirectoryContext:
    dir_name = x_directory
    if not dir_name:
        raise HTTPException(status_code=400, detail=f'missing {DIRECTORY_NAME_HEADER} header')
    try:
        return directory_context_holder.get_context(dir_name)
    except Exception as e:
        logger.error(f'failed to get context for {dir_name}', exc_info=e)
        raise HTTPException(status_code=404, detail=f'directory {DIRECTORY_NAME_HEADER} not available')
    
def get_root_dir_path(ctx: Annotated[DirectoryContext, Depends(get_directory_context)]) -> Path:
    return ctx.root_dir

async def get_session(ctx: Annotated[DirectoryContext, Depends(get_directory_context)]) -> AsyncGenerator[AsyncSession, None]:
    async with ctx.db.session() as sess:
        async with sess.begin():
            yield sess

async def get_directories_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with app_db.session() as sess:
        async with sess.begin():
            yield sess

async def get_file_repo(session: Annotated[AsyncSession, Depends(get_session)]):
    return FileMetadataRepository(session)

async def get_directory_repo(session: Annotated[AsyncSession, Depends(get_directories_db_session)]):
    return DirectoryRepository(session)

def get_thumbnail_manager(ctx: Annotated[DirectoryContext, Depends(get_directory_context)]) -> ThumbnailManager:
    return ctx.thumbnail_manager

def get_mapper(thumbnail_manager: Annotated[ThumbnailManager, Depends(get_thumbnail_manager)]) -> Mapper:
    return Mapper(thumbnail_manager)

def get_metadata_editor(
    ctx: Annotated[DirectoryContext, Depends(get_directory_context)],
    file_repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]
) -> MetadataEditor:
    return ctx.get_metadata_editor(file_repo)

def get_search_service(
    ctx: Annotated[DirectoryContext, Depends(get_directory_context)],
    file_repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]
) -> SearchService:
    return ctx.get_search_service(file_repo)

async def teardown():
    await directory_context_holder.teardown()
