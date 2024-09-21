

from persistence.file_metadata_repository import FileMetadataRepository
from search.lemmatizer import Lemmatizer
from search.lexical_search_engine import LexicalSearchEngine
from search.reverse_index import ReverseIndex
from search.token_stat_counter import TokenStatCounter


class LexicalSearchEngineInitializer:
    def __init__(self, lemmatizer: Lemmatizer, file_repo: FileMetadataRepository) -> None:
        self.lemmatizer = lemmatizer
        self.file_repo = file_repo
        self.description_lexical_search_engine = self._make_lexical_search_engine()
        self.ocr_text_lexical_search_engine = self._make_lexical_search_engine()
        self.transcript_lexical_search_engine = self._make_lexical_search_engine()

    async def init_search_engines(self):
        files = await self.file_repo.load_all_files()

        for file in files:
            fid = int(file.id)
            dirty = False
            if file.description != '':
                if file.lemmatized_description is None:
                    file.lemmatized_description = self._lemmatize_and_join(file.description)
                    dirty = True
                self._split_and_register(self.description_lexical_search_engine, file.lemmatized_description, fid)
            
            if file.is_ocr_analyzed and file.ocr_text is not None and file.ocr_text != '':
                if file.lemmatized_ocr_text is None:
                    file.lemmatized_ocr_text = self._lemmatize_and_join(file.ocr_text)
                    dirty = True
                self._split_and_register(self.ocr_text_lexical_search_engine, file.lemmatized_ocr_text, fid)
            
            if file.is_transcript_analyzed and file.transcript is not None and file.transcript != '':
                if file.lemmatized_transcript is None:
                    file.lemmatized_transcript = self._lemmatize_and_join(file.transcript)
                    dirty = True
                self._split_and_register(self.transcript_lexical_search_engine, file.lemmatized_transcript, fid)

            if dirty:
                await self.file_repo.update_file(file)

    def _split_and_register(self, engine: LexicalSearchEngine, text: str, file_id: int):
        tokens = text.split()
        for token in text.split():
            engine.reverse_index.add_entry(token, file_id)
        engine.token_stat_counter.register(tokens, file_id)
    
    def _lemmatize_and_join(self, text: str):
        return ' '.join(self.lemmatizer.lemmatize(str(text)))

    def _make_lexical_search_engine(self):
        return LexicalSearchEngine(self.lemmatizer, ReverseIndex(), TokenStatCounter())
