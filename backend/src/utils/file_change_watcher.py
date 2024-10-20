import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from watchdog.events import (DirCreatedEvent, DirDeletedEvent, FileClosedEvent,
                             FileCreatedEvent, FileDeletedEvent,
                             FileSystemEventHandler)
from watchdog.observers import Observer

FileCreatedObserver = Callable[[Path], Awaitable[None]]
FileDeletedObserver = FileCreatedObserver

class FileChangeWatcher:
    def __init__(self, root_dir: Path, file_created_observer: FileCreatedObserver, file_deleted_observer: FileDeletedObserver):
        self.root_dir = root_dir
        self.file_created_observer = file_created_observer
        self.file_deleted_observer = file_deleted_observer
        self.observer = None
        self.callback_loop = None

    class WatchdogEventHandler(FileSystemEventHandler):
        def __init__(self, wrapper: "FileChangeWatcher"):
            super().__init__()
            self.wrapper = wrapper
            # file created event is sent right after file creation (the inode creation), before
            # it was actually written, we should mark such files and call on_create after they were fully written
            # which we can detect by awaiting file close event after file create event
            self.awaiting_file_writes = set()

        def on_created(self, event: FileCreatedEvent | DirCreatedEvent):
            if event.is_directory:
                return # ignore directories
            path = Path(event.src_path)
            self.awaiting_file_writes.add(path.name)

        def on_closed(self, event: FileClosedEvent):
            if event.is_directory:
                return # ignore directories
            path = Path(event.src_path)
            if path.name in self.awaiting_file_writes:
                self.awaiting_file_writes.remove(path.name)
                self.wrapper._on_created(path)

        def on_deleted(self, event: FileDeletedEvent | DirDeletedEvent):
            if event.is_directory:
                return # ignore directories
            self.wrapper._on_deleted(Path(event.src_path))

    def start_watcher_thread(self, loop: asyncio.AbstractEventLoop):
        self.callback_loop = loop
        handler = self.WatchdogEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.root_dir.absolute()), recursive=False, event_filter=[FileCreatedEvent, FileDeletedEvent, FileClosedEvent])
        self.observer.start()

    def _on_created(self, path: Path):
        self.callback_loop.call_soon_threadsafe(lambda: self.callback_loop.create_task(self.file_created_observer(path)))

    def _on_deleted(self, path: Path):
        self.callback_loop.call_soon_threadsafe(lambda: self.callback_loop.create_task(self.file_deleted_observer(path)))

    def stop(self):
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
