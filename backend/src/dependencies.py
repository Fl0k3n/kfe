import asyncio
import gzip
import os
from pathlib import Path

import easyocr
import msgpack
import torch
import wordfreq
from huggingsound import Decoder as SpeechDecoder
from huggingsound import SpeechRecognitionModel
from sentence_transformers import SentenceTransformer
from transformers import (AutoImageProcessor, AutoModel, CLIPModel,
                          CLIPProcessor)

from dtos.mappers import Mapper
from features.audioutils.dictionary_assisted_decoder import \
    DictionaryAssistedDecoder
from features.clip_engine import CLIPEngine
from features.image_embedding_engine import ImageEmbeddingEngine
from features.ocr_engine import OCREngine
from features.text_embedding_engine import TextEmbeddingEngine
from features.transcriber import Transcriber
from persistence.db import Database
from persistence.embeddings import EmbeddingPersistor
from persistence.file_metadata_repository import FileMetadataRepository
from search.lemmatizer import Lemmatizer
from search.query_parser import SearchQueryParser
from service.embedding_processor import EmbeddingProcessor
from service.file_change_handler import FileChangeHandler
from service.file_indexer import FileIndexer
from service.metadata_editor import MetadataEditor
from service.ocr_service import OCRService
from service.search import SearchService
from service.thumbnails import ThumbnailManager
from service.transcription_service import TranscriptionService
from utils.constants import PRELOAD_THUMBNAILS_ENV
from utils.datastructures.bktree import BKTree
from utils.datastructures.trie import Trie
from utils.file_change_watcher import FileChangeWatcher
from utils.lexical_search_engine_initializer import \
    LexicalSearchEngineInitializer
from utils.log import logger
from utils.model_manager import ModelManager, ModelType
from utils.persistence import dump_descriptions, restore_descriptions

# ROOT_DIR = Path('/home/flok3n/minikonrad'); DB_DIR = Path('.')
ROOT_DIR = Path('/home/flok3n/konrad'); DB_DIR = ROOT_DIR
LANGUAGES = ['pl', 'en']
SRC_DIR = Path(__file__).parent

db = Database(DB_DIR)
file_repo = FileMetadataRepository(db)
file_indexer = FileIndexer(ROOT_DIR, file_repo)
thumbnail_manager = ThumbnailManager(ROOT_DIR)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if not torch.cuda.is_available():
    logger.warning('cuda unavailable')

def get_text_embedding_model():
    return SentenceTransformer('ipipan/silver-retriever-base-v1.1').to(device)

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
    ModelType.OCR: lambda: easyocr.Reader([*LANGUAGES], gpu=True),
    ModelType.TRANSCRIBER: get_transcription_model,
    ModelType.TEXT_EMBEDDING: get_text_embedding_model,
    ModelType.IMAGE_EMBEDDING: get_image_embedding_model,
    ModelType.CLIP: get_clip_model,
})

mapper = Mapper(thumbnail_manager)

lemmatizer = Lemmatizer()
lexical_search_initializer = LexicalSearchEngineInitializer(lemmatizer, file_repo)

text_embedding_engine = TextEmbeddingEngine(model_manager, query_prefix='Pytanie: ', passage_prefix='</s>')
image_embedding_engine = ImageEmbeddingEngine(model_manager, device)
clip_engine = CLIPEngine(model_manager, device)
embedding_persistor = EmbeddingPersistor(ROOT_DIR)
embedding_processor = EmbeddingProcessor(ROOT_DIR, file_repo, embedding_persistor, text_embedding_engine, image_embedding_engine, clip_engine)

ocr_engine = OCREngine(model_manager, LANGUAGES)
ocr_service = OCRService(ROOT_DIR, file_repo, ocr_engine)

transcriber = Transcriber(model_manager)
transcription_service = TranscriptionService(ROOT_DIR, transcriber, file_repo)

query_parser = SearchQueryParser()

search_service = SearchService(
    file_repo,
    query_parser,
    lexical_search_initializer.description_lexical_search_engine,
    lexical_search_initializer.ocr_text_lexical_search_engine,
    lexical_search_initializer.transcript_lexical_search_engine,
    embedding_processor,
)

metadata_editor = MetadataEditor(
    file_repo,
    lexical_search_initializer.description_lexical_search_engine,
    lexical_search_initializer.transcript_lexical_search_engine,
    embedding_processor,
)

file_change_handler = FileChangeHandler(file_repo, file_indexer, embedding_processor, ocr_service, transcription_service, thumbnail_manager)
file_change_watcher = FileChangeWatcher(ROOT_DIR, file_change_handler.on_file_created, file_change_handler.on_file_deleted)

async def init(should_dump_descriptions=False, should_restore_descriptions=False):
    logger.info('initializing database')
    await db.init_db()

    logger.info('initializg file change watcher')
    file_change_watcher.start_watcher_thread(asyncio.get_running_loop())

    logger.info('ensuring directory initialized')
    num_previously_stored_files = await file_indexer.ensure_directory_initialized()

    description_dump_path = ROOT_DIR.joinpath('description_dump.json')
    if should_restore_descriptions:
        logger.info(f'restoring descriptions from {description_dump_path}')
        await restore_descriptions(description_dump_path, db)
    if num_previously_stored_files > 0 and should_dump_descriptions:
        logger.info(f'dumping descriptions to {description_dump_path}')
        await dump_descriptions(description_dump_path, file_repo)

    logger.info('initializing OCR services')
    await ocr_service.init_ocrs()

    logger.info('initializing transcription services')
    await transcription_service.init_transcriptions(retranscribe_all_auto_trancribed=False)

    logger.info('initializing lexical search engines')
    await lexical_search_initializer.init_search_engines()

    logger.info('initalizing embeddings')
    with (
        model_manager.use(ModelType.TEXT_EMBEDDING),
        model_manager.use(ModelType.IMAGE_EMBEDDING),
        model_manager.use(ModelType.CLIP)
    ):
        await embedding_processor.init_embeddings()
    
    if os.getenv(PRELOAD_THUMBNAILS_ENV, 'false') == 'true':
        logger.info('preloading thumbnails')
        await thumbnail_manager.preload_thumbnails(await file_repo.load_all_files())

    logger.info('application ready')

async def teardown():
    await db.close_db()
    file_change_watcher.stop()

def get_file_repo() -> FileMetadataRepository:
    return file_repo

def get_thumbnail_manager() -> ThumbnailManager:
    return thumbnail_manager

def get_search_service() -> SearchService:
    return search_service

def get_mapper() -> Mapper:
    return mapper

def get_metadata_editor() -> MetadataEditor:
    return metadata_editor

def get_model_manager() -> ModelManager:
    return model_manager
