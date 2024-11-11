import asyncio
import gzip
import os
from pathlib import Path
from typing import Annotated, AsyncGenerator, Optional
from unittest.mock import patch

import easyocr
import msgpack
import torch
import wordfreq
from fastapi import Depends, Header, HTTPException
from huggingsound import Decoder as SpeechDecoder
from huggingsound import SpeechRecognitionModel
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import (AutoImageProcessor, AutoModel, AutoModelForCTC,
                          CLIPModel, CLIPProcessor, Wav2Vec2Processor)

from directory_context import DirectoryContext, DirectoryContextHolder
from dtos.mappers import Mapper
from features.audioutils.dictionary_assisted_decoder import \
    DictionaryAssistedDecoder
from features.text_embedding_engine import TextModelWithConfig
from persistence.db import Database
from persistence.directory_repository import DirectoryRepository
from persistence.file_metadata_repository import FileMetadataRepository
from search.lemmatizer import Lemmatizer
from search.query_parser import SearchQueryParser
from service.metadata_editor import MetadataEditor
from service.search import SearchService
from service.thumbnails import ThumbnailManager
from utils.constants import (DEVICE_ENV, DIRECTORY_NAME_HEADER, LOG_SQL_ENV,
                             SUPPORTED_LANGUAGES, Language)
from utils.datastructures.bktree import BKTree
from utils.datastructures.trie import Trie
from utils.log import logger
from utils.model_cache import try_loading_cached_or_download
from utils.model_manager import ModelManager, ModelType, SecondaryModelManager

SRC_DIR = Path(__file__).parent
REFRESH_PERIOD_SECONDS = 3600 * 24.

device = torch.device('cuda' if torch.cuda.is_available() and os.getenv(DEVICE_ENV, 'cuda') == 'cuda' else 'cpu')
if not torch.cuda.is_available():
    logger.warning('cuda unavailable')

def get_text_embedding_model(language: Language):
    return TextModelWithConfig(
        model=try_loading_cached_or_download(
            'ipipan/silver-retriever-base-v1.1' if language == 'pl' else 'sentence-transformers/all-mpnet-base-v2',
            lambda x: SentenceTransformer(x.model_path, cache_folder=x.cache_dir, local_files_only=x.local_files_only)
        ).to(device),
        query_prefix='Pytanie: ' if language == 'pl' else '',
        passage_prefix='</s>' if language == 'pl' else ''
    )

def get_image_embedding_model() -> tuple[AutoImageProcessor, AutoModel]:
    processor = try_loading_cached_or_download(
        "google/vit-base-patch16-224-in21k",
        lambda x: AutoImageProcessor.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
    )
    model = try_loading_cached_or_download(
        "google/vit-base-patch16-224-in21k",
        lambda x: AutoModel.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
    ).to(device)
    return processor, model

def get_clip_model() -> tuple[CLIPProcessor, CLIPModel]:
    clip_processor = try_loading_cached_or_download(
        "openai/clip-vit-base-patch32",
        lambda x: CLIPProcessor.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
    )
    clip_model = try_loading_cached_or_download(
        "openai/clip-vit-base-patch32",
        lambda x: CLIPModel.from_pretrained(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
    ).to(device)
    return clip_processor, clip_model

def get_transcription_model_not_finetuned(language: Language) -> tuple[SpeechRecognitionModel, Optional[SpeechDecoder]]:
    # huggingsound library doesn't allow bypassing sending requests to huggingface while loading the model
    # and as a result transcription wouldn't work offline even if model was downloaded before, the code below
    # makes some workarounds
    model_from_pretrained_before_patch = AutoModelForCTC.from_pretrained
    processor_from_pretrained_before_patch = Wav2Vec2Processor.from_pretrained
    def load_auto_model_for_ctc(model_id: str):
        return try_loading_cached_or_download(
            model_id,
            lambda x: model_from_pretrained_before_patch(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
        )
    def load_wav2Vec2Processor(model_id: str):
        return try_loading_cached_or_download(
            model_id,
            lambda x: processor_from_pretrained_before_patch(x.model_path, cache_dir=x.cache_dir, local_files_only=x.local_files_only)
        )
    with (
        patch('huggingsound.speech_recognition.model.AutoModelForCTC.from_pretrained', load_auto_model_for_ctc),
        patch('huggingsound.speech_recognition.model.Wav2Vec2Processor.from_pretrained', load_wav2Vec2Processor)
    ):
        lang = 'polish' if language == 'pl' else 'english'
        model = SpeechRecognitionModel(f"jonatasgrosman/wav2vec2-large-xlsr-53-{lang}", device=str(device))
        return model, None

def get_transcription_model_finetuned() -> tuple[SpeechRecognitionModel, Optional[SpeechDecoder]]:
    with gzip.open(wordfreq.DATA_PATH.joinpath('large_pl.msgpack.gz'), 'rb') as f:
        dictionary_data = msgpack.load(f, raw=False)
    try:
        model = SpeechRecognitionModel(SRC_DIR.joinpath('finetuning').joinpath('models'), device=str(device))
    except (FileNotFoundError, EnvironmentError) as e:
        logger.warning(f'failed to load finetuned transcription model, loading default', exc_info=e)
        model, _ = get_transcription_model_not_finetuned('pl')
    tokens = [*model.token_set.non_special_tokens]
    token_id_lut = {x: i for i, x in enumerate(tokens)}

    dictionary_trie = Trie(len(tokens))
    correction_bkt = BKTree(root_word='kurwa')

    for bucket in dictionary_data[1:]:
        for word in bucket:
            try:
                tokenized_word = [token_id_lut[x] for x in word]
                dictionary_trie.add(tokenized_word)
                correction_bkt.add(word)
            except KeyError:
                pass # ignore word
    
    decoder = DictionaryAssistedDecoder(model.token_set, dictionary_trie, correction_bkt, token_id_lut)
    return model, decoder

pl_model_manager = ModelManager(model_providers={
    ModelType.OCR: lambda: easyocr.Reader([*SUPPORTED_LANGUAGES], gpu=os.getenv(DEVICE_ENV, 'cuda') == 'cuda'),
    ModelType.TRANSCRIBER: get_transcription_model_finetuned,
    ModelType.TEXT_EMBEDDING: lambda: get_text_embedding_model('pl'),
    ModelType.IMAGE_EMBEDDING: get_image_embedding_model,
    ModelType.CLIP: get_clip_model,
})

en_model_manager = SecondaryModelManager(primary=pl_model_manager, owned_model_providers={
    ModelType.TRANSCRIBER: lambda: get_transcription_model_not_finetuned('en'),
    ModelType.TEXT_EMBEDDING: lambda: get_text_embedding_model('en'),
})

model_managers = {
    'pl': pl_model_manager,
    'en': en_model_manager,
}

pl_lemmatizer = Lemmatizer(model='pl_core_news_lg')
en_lemmatizer = Lemmatizer(model='en_core_web_lg')

directory_context_holder = DirectoryContextHolder(
    model_managers=model_managers,
    lemmatizers={
        'pl': pl_lemmatizer,
        'en': en_lemmatizer,
    },
    device=device
)

app_db = Database(SRC_DIR, log_sql=os.getenv(LOG_SQL_ENV, 'true') == 'true')

async def init():
    logger.info(f'initializing shared app db in directory: {SRC_DIR}')
    await app_db.init_db()
    async def init_directories_in_background():
        async with app_db.session() as sess:
            registered_directories = await DirectoryRepository(sess).get_all()
        for directory in registered_directories:
            logger.info(f'initializing registered directory: {directory.name}, from: {directory.path}')
            try:
                await directory_context_holder.register_directory(directory.name, directory.path, directory.primary_language, directory.languages)
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
            await directory_context_holder.register_directory(directory.name, directory.path, directory.primary_language, directory.languages)
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
    return MetadataEditor(
        file_repo,
        ctx.lexical_search_initializer.description_lexical_search_engine,
        ctx.lexical_search_initializer.transcript_lexical_search_engine,
        ctx.lexical_search_initializer.ocr_text_lexical_search_engine,
        ctx.embedding_processor,
    )

def get_search_service(
    ctx: Annotated[DirectoryContext, Depends(get_directory_context)],
    file_repo: Annotated[FileMetadataRepository, Depends(get_file_repo)]
) -> SearchService:
    return SearchService(
        file_repo,
        SearchQueryParser(),
        ctx.lexical_search_initializer.description_lexical_search_engine,
        ctx.lexical_search_initializer.ocr_text_lexical_search_engine,
        ctx.lexical_search_initializer.transcript_lexical_search_engine,
        ctx.embedding_processor,
    )

async def teardown():
    await directory_context_holder.teardown()
