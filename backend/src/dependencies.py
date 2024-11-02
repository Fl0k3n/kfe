import gzip
from pathlib import Path
from typing import Annotated, AsyncGenerator

import easyocr
import msgpack
import torch
import wordfreq
from fastapi import Depends, Header, HTTPException, Request
from huggingsound import Decoder as SpeechDecoder
from huggingsound import SpeechRecognitionModel
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import (AutoImageProcessor, AutoModel, CLIPModel,
                          CLIPProcessor)

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
from utils.constants import DIRECTORY_NAME_HEADER
from utils.datastructures.bktree import BKTree
from utils.datastructures.trie import Trie
from utils.log import logger
from utils.model_manager import ModelManager, ModelType

OCR_LANGUAGES = ['pl', 'en']
SRC_DIR = Path(__file__).parent

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if not torch.cuda.is_available():
    logger.warning('cuda unavailable')

def get_text_embedding_model():
    return TextModelWithConfig(
        model=SentenceTransformer('ipipan/silver-retriever-base-v1.1').to(device),
        query_prefix='Pytanie: ',
        passage_prefix='</s>'
    )

def get_image_embedding_model() -> tuple[AutoImageProcessor, AutoModel]:
    processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
    model = AutoModel.from_pretrained("google/vit-base-patch16-224-in21k").to(device)
    return processor, model

def get_clip_model() -> tuple[CLIPProcessor, CLIPModel]:
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    return clip_processor, clip_model

def get_transcription_model() -> tuple[SpeechRecognitionModel, SpeechDecoder]:
    with gzip.open(wordfreq.DATA_PATH.joinpath('large_pl.msgpack.gz'), 'rb') as f:
        dictionary_data = msgpack.load(f, raw=False)
    # model = SpeechRecognitionModel("jonatasgrosman/wav2vec2-large-xlsr-53-polish", device=str(device))
    model = SpeechRecognitionModel(SRC_DIR.joinpath('finetuning').joinpath('models'), device=str(device))
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

model_manager = ModelManager(model_providers={
    ModelType.OCR: lambda: easyocr.Reader([*OCR_LANGUAGES], gpu=True),
    ModelType.TRANSCRIBER: get_transcription_model,
    ModelType.TEXT_EMBEDDING: get_text_embedding_model,
    ModelType.IMAGE_EMBEDDING: get_image_embedding_model,
    ModelType.CLIP: get_clip_model,
})

lemmatizer = Lemmatizer()

directory_context_holder = DirectoryContextHolder(model_manager, lemmatizer, device)

app_db = Database(SRC_DIR, log_sql=True)

async def init():
    logger.info(f'initializing shared app db in directory: {SRC_DIR}')
    await app_db.init_db()
    async with app_db.session() as sess:
        registered_directories = await DirectoryRepository(sess).get_all()
    for directory in registered_directories:
        logger.info(f'initializing registered directory: {directory.name}, from: {directory.path}')
        try:
            await directory_context_holder.register_directory(directory.name, directory.path, directory.languages)
        except Exception as e:
            logger.error(f'Failed to initialize directory: {directory.name}', exc_info=e)

def get_model_manager() -> ModelManager:
    return model_manager

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
