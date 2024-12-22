
from enum import Enum
from typing import NamedTuple


class InitStateInfo(NamedTuple):
    description: str
    weight: float

class InitState(InitStateInfo, Enum):
    # weights must sum to 1
    OCR = InitStateInfo("Extracting text from images", 0.2)
    TRANSCIPTION = InitStateInfo("Extracting speech from audio files", 0.35)
    LEXICAL = InitStateInfo("Setting up text search structures", 0.05)
    EMBEDDING = InitStateInfo("Initializing embeddings", 0.35)
    THUMBNAILS = InitStateInfo("Initializing file thumbnails", 0.05)

class InitProgressTracker:
    def __init__(self):
        self.current_state: InitState = None
        self.total_files_to_process = 0
        self.processed_files = 0
        self.running_progress = 0.
        self.ready = False

    def enter_state(self, state: InitState, total_files_to_process: int):
        if self.current_state is not None:
            self.running_progress += self.current_state.weight
        self.processed_files = 0
        self.current_state = state
        self.total_files_to_process = total_files_to_process

    def mark_file_processed(self):
        self.processed_files += 1

    def get_progress_status(self) -> tuple[str, float]:
        if self.ready:
            return "Ready", 1.
        if self.current_state is None:
            return "Initializing structures", 0.
        state_progress = 0.
        if self.total_files_to_process != 0:
            state_progress = min(self.processed_files / self.total_files_to_process, 1.)
        return (
            f'{self.current_state.description}, processed {self.processed_files} / {self.total_files_to_process} files.',
            min(self.running_progress + self.current_state.weight * state_progress, 1.)
        )

    def set_ready(self):
        self.ready = True
