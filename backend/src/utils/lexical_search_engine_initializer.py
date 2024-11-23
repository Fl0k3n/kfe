from features.lemmatizer import Lemmatizer
from persistence.file_metadata_repository import FileMetadataRepository
from search.lexical_search_engine import LexicalSearchEngine
from search.reverse_index import ReverseIndex
from search.token_stat_counter import TokenStatCounter
from utils.init_progress_tracker import InitProgressTracker, InitState


class LexicalSearchEngineInitializer:
    def __init__(self, lemmatizer: Lemmatizer, file_repo: FileMetadataRepository) -> None:
        self.lemmatizer = lemmatizer
        self.file_repo = file_repo
        self.description_lexical_search_engine = self._make_lexical_search_engine()
        self.ocr_text_lexical_search_engine = self._make_lexical_search_engine()
        self.transcript_lexical_search_engine = self._make_lexical_search_engine()

    async def init_search_engines(self, progress_tracker: InitProgressTracker):
        files = await self.file_repo.load_all_files()
        progress_tracker.enter_state(InitState.LEXICAL, len(files))

        async with self.lemmatizer.run() as engine:
            for file in files:
                fid = int(file.id)
                dirty = False
                if file.description != '':
                    if file.lemmatized_description is None:
                        file.lemmatized_description = await self._lemmatize_and_join(engine, file.description)
                        dirty = True
                    self._split_and_register(self.description_lexical_search_engine, file.lemmatized_description, fid)
                
                if file.is_ocr_analyzed and file.ocr_text is not None and file.ocr_text != '':
                    if file.lemmatized_ocr_text is None:
                        file.lemmatized_ocr_text = await self._lemmatize_and_join(engine, file.ocr_text)
                        dirty = True
                    self._split_and_register(self.ocr_text_lexical_search_engine, file.lemmatized_ocr_text, fid)
                
                if file.is_transcript_analyzed and file.transcript is not None and file.transcript != '':
                    if file.lemmatized_transcript is None:
                        file.lemmatized_transcript = await self._lemmatize_and_join(engine, file.transcript)
                        dirty = True
                    self._split_and_register(self.transcript_lexical_search_engine, file.lemmatized_transcript, fid)

                if dirty:
                    await self.file_repo.update_file(file)
                progress_tracker.mark_file_processed()

    def _split_and_register(self, engine: LexicalSearchEngine, text: str, file_id: int):
        tokens = text.split()
        for token in tokens:
            engine.reverse_index.add_entry(token, file_id)
        engine.token_stat_counter.register(tokens, file_id)
    
    async def _lemmatize_and_join(self, lemmatizer_engine: Lemmatizer.Engine, text: str) -> list[str]:
        return ' '.join(await lemmatizer_engine.lemmatize(str(text)))

    def _make_lexical_search_engine(self) -> LexicalSearchEngine:
        return LexicalSearchEngine(self.lemmatizer, ReverseIndex(), TokenStatCounter())

