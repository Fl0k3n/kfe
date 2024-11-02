from typing import Optional

from persistence.file_metadata_repository import FileMetadataRepository
from persistence.model import FileMetadata
from search.lexical_search_engine import LexicalSearchEngine
from service.embedding_processor import EmbeddingProcessor


class MetadataEditor:
    def __init__(self, file_repo: FileMetadataRepository,
                 description_lexical_search_engine: LexicalSearchEngine,
                 transcript_lexical_search_engine: LexicalSearchEngine,
                 ocr_lexical_search_engine: LexicalSearchEngine,
                 embedding_processor: EmbeddingProcessor) -> None:
        self.file_repo = file_repo
        self.description_lexical_search_engine = description_lexical_search_engine
        self.transcript_lexical_search_engine = transcript_lexical_search_engine
        self.ocr_lexical_search_engine = ocr_lexical_search_engine
        self.embedding_processor = embedding_processor

    async def update_description(self, file: FileMetadata, new_description: str):
        fid = int(file.id)
        old_description = str(file.description)
        file.lemmatized_description = self._update_lexical_structures_and_get_lemmatized_text(
            fid,
            new_description,
            str(file.lemmatized_description) if file.lemmatized_description is not None else None,
            self.description_lexical_search_engine
        )
        file.description = new_description
        await self.embedding_processor.update_description_embedding(file, old_description)
        await self.file_repo.update_file(file)

    async def update_transcript(self, file: FileMetadata, new_transcript: str):
        fid = int(file.id)
        old_transcript = str(file.transcript)
        file.lemmatized_transcript = self._update_lexical_structures_and_get_lemmatized_text(
            fid,
            new_transcript,
            str(file.lemmatized_transcript) if file.lemmatized_transcript is not None else None,
            self.transcript_lexical_search_engine
        )
        file.transcript = new_transcript
        file.is_transcript_fixed = True
        await self.embedding_processor.update_transcript_embedding(file, old_transcript)
        await self.file_repo.update_file(file)

    async def update_ocr_text(self, file: FileMetadata, new_ocr_text: str):
        fid = int(file.id)
        old_ocr_text = str(file.ocr_text)
        file.lemmatized_ocr_text = self._update_lexical_structures_and_get_lemmatized_text(
            fid,
            new_ocr_text,
            str(file.lemmatized_ocr_text) if file.lemmatized_ocr_text is not None else None,
            self.ocr_lexical_search_engine
        )
        file.ocr_text = new_ocr_text
        await self.embedding_processor.update_ocr_text_embedding(file, old_ocr_text)
        await self.file_repo.update_file(file)

    def _update_lexical_structures_and_get_lemmatized_text(self, file_id: int, new_text: str,
            old_lemmatized_text: Optional[str], search_engine: LexicalSearchEngine) -> Optional[str]:
        if old_lemmatized_text is not None and old_lemmatized_text != '':
            old_tokens = old_lemmatized_text.split()
            for token in set(old_tokens):
                search_engine.reverse_index.remove_entry(token, file_id)
            search_engine.token_stat_counter.unregister(old_tokens, file_id)
        if new_text == '':
            return None
        new_lemmatized_tokens = search_engine.lemmatizer.lemmatize(new_text)
        for token in new_lemmatized_tokens:
            search_engine.reverse_index.add_entry(token, file_id)
        search_engine.token_stat_counter.register(new_lemmatized_tokens, file_id)
        return ' '.join(new_lemmatized_tokens)
