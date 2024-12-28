from typing import Optional

from sqlalchemy import Column

from kfe.features.lemmatizer import Lemmatizer
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata
from kfe.search.lexical_search_engine import LexicalSearchEngine, LexicalTokens
from kfe.search.tokenizer import tokenize_text
from kfe.service.embedding_processor import EmbeddingProcessor


class MetadataEditor:
    def __init__(self, file_repo: FileMetadataRepository,
                 description_lexical_search_engine: LexicalSearchEngine,
                 transcript_lexical_search_engine: LexicalSearchEngine,
                 ocr_lexical_search_engine: LexicalSearchEngine,
                 embedding_processor: EmbeddingProcessor,
                 lemmatizer: Lemmatizer) -> None:
        self.file_repo = file_repo
        self.description_lexical_search_engine = description_lexical_search_engine
        self.transcript_lexical_search_engine = transcript_lexical_search_engine
        self.ocr_lexical_search_engine = ocr_lexical_search_engine
        self.embedding_processor = embedding_processor
        self.lemmatizer = lemmatizer

    async def update_description(self, file: FileMetadata, new_description: str):
        old_description = str(file.description)
        file.lemmatized_description = await self._update_lexical_structures_and_get_lemmatized_text(
            file.id,
            new_description,
            old_description,
            file.lemmatized_description,
            self.description_lexical_search_engine
        )
        file.description = new_description
        await self.embedding_processor.update_description_embedding(file, old_description)
        await self.file_repo.update_file(file)

    async def update_transcript(self, file: FileMetadata, new_transcript: str):
        old_transcript = str(file.transcript)
        file.lemmatized_transcript = await self._update_lexical_structures_and_get_lemmatized_text(
            file.id,
            new_transcript,
            old_transcript,
            file.lemmatized_transcript,
            self.transcript_lexical_search_engine
        )
        file.transcript = new_transcript
        file.is_transcript_fixed = True
        await self.embedding_processor.update_transcript_embedding(file, old_transcript)
        await self.file_repo.update_file(file)

    async def update_ocr_text(self, file: FileMetadata, new_ocr_text: str):
        old_ocr_text = str(file.ocr_text)
        file.lemmatized_ocr_text = await self._update_lexical_structures_and_get_lemmatized_text(
            file.id,
            new_ocr_text,
            old_ocr_text,
            file.lemmatized_ocr_text,
            self.ocr_lexical_search_engine
        )
        file.ocr_text = new_ocr_text
        await self.embedding_processor.update_ocr_text_embedding(file, old_ocr_text)
        await self.file_repo.update_file(file)

    async def update_screenshot_type(self, file: FileMetadata, is_screenshot: bool):
        if file.is_screenshot:
            await self.update_ocr_text(file, '')
        else:
            file.ocr_text = ''
        file.is_screenshot = is_screenshot
        await self.file_repo.update_file(file)

    async def on_file_created(self, file: FileMetadata):
        if file.description != '':
            file.lemmatized_description = await self._update_lexical_structures_and_get_lemmatized_text(
                file.id, file.description, None, None, self.description_lexical_search_engine)
        if file.is_transcript_analyzed and file.transcript is not None and file.transcript != '':
            file.lemmatized_transcript = await self._update_lexical_structures_and_get_lemmatized_text(
                file.id, file.transcript, None, None, self.transcript_lexical_search_engine)
        if file.is_ocr_analyzed and file.ocr_text is not None and file.ocr_text != '':
            file.lemmatized_ocr_text = await self._update_lexical_structures_and_get_lemmatized_text(
                file.id, file.ocr_text, None, None, self.ocr_lexical_search_engine)

    async def on_file_deleted(self, file: FileMetadata):
        await self._update_lexical_structures_and_get_lemmatized_text(
            file.id, None, file.description, file.lemmatized_description, self.description_lexical_search_engine)
        await self._update_lexical_structures_and_get_lemmatized_text(
            file.id, None, file.transcript, file.lemmatized_transcript, self.transcript_lexical_search_engine)
        await self._update_lexical_structures_and_get_lemmatized_text(
            file.id, None, file.ocr_text, file.lemmatized_ocr_text, self.ocr_lexical_search_engine)

    async def _update_lexical_structures_and_get_lemmatized_text(self, file_id: int | Column[int], new_text: Optional[str | Column[str]], 
            old_text: Optional[str | Column[str]], old_lemmatized_text: Optional[str | Column[str]], search_engine: LexicalSearchEngine) -> Optional[str]:
        if old_lemmatized_text is not None and old_text is not None and old_text != '':
            search_engine.unregister_tokens(LexicalTokens(
                original=tokenize_text(str(old_text)),
                lemmatized=str(old_lemmatized_text).split()
            ), int(file_id))
        if new_text is None or new_text == '':
            return None
        async with self.lemmatizer.run() as engine:
            new_lemmatized_tokens = await engine.lemmatize(new_text)
        search_engine.register_tokens(
            LexicalTokens(
                original=tokenize_text(str(new_text)),
                lemmatized=new_lemmatized_tokens
            ), int(file_id))
        return ' '.join(new_lemmatized_tokens)
