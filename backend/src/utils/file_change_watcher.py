import asyncio
import queue
import threading
from pathlib import Path
from typing import Awaitable, Callable

from watchdog.events import (DirCreatedEvent, DirDeletedEvent, FileClosedEvent,
                             FileCreatedEvent, FileDeletedEvent,
                             FileMovedEvent, FileOpenedEvent,
                             FileSystemEventHandler)
from watchdog.observers import Observer

FileCreatedObserver = Callable[[Path], Awaitable[None]]
FileDeletedObserver = FileCreatedObserver
FileMovedObserver = Callable[[Path, Path], Awaitable[None]] # (old, new)

class FileChangeWatcher:
    def __init__(self, root_dir: Path, file_created_observer: FileCreatedObserver,
                 file_deleted_observer: FileDeletedObserver, file_moved_observer: FileMovedObserver,
                 ignored_files: set[str] = None):
        self.root_dir = root_dir
        self.file_created_observer = file_created_observer
        self.file_deleted_observer = file_deleted_observer
        self.file_moved_observer = file_moved_observer
        self.ignored_files = ignored_files if ignored_files is not None else set()
        self.observer = None
        self.callback_loop = None
        self.handler = None

    class WatchdogEventHandler(FileSystemEventHandler):
        WAIT_FOR_OPEN_SECONDS = 1.

        def __init__(self, wrapper: "FileChangeWatcher"):
            super().__init__()
            self.wrapper = wrapper
            self.sets_lock = threading.Lock()
            self.create_paths: set[str] = set()
            self.open_paths: set[str] = set()
            self.close_paths: set[str] = set()

            self.check_paths_queue: queue.Queue[Path] = queue.SimpleQueue()
            self.sleep_event = threading.Event()

            threading.Thread(target=self._open_event_checker_thread).start()

        def _open_event_checker_thread(self):
            while True:
                task = self.check_paths_queue.get()
                if task is None:
                    return # poison pill
                interrupted = self.sleep_event.wait(timeout=self.WAIT_FOR_OPEN_SECONDS)
                if interrupted:
                    return
                with self.sets_lock:
                    if task.name in self.create_paths and task.name not in self.open_paths:
                        # it was created but wasn't opened, so it was likely move -> disptach on_create
                        self.create_paths.remove(task.name)
                        self.wrapper._on_created(task)

        def on_created(self, event: FileCreatedEvent | DirCreatedEvent):
            if event.is_directory:
                return # ignore directories
            path = Path(event.src_path)
            # files system move operation doesn't open nor close the file,
            # in such case we should immediately trigger wrapper._on_created.
            # File creation (e.g. manual write, copy), on the other hand, requires
            # both open and close, and we should wait for close before we call wrapper, so it can read
            # ready file. For this use case we use a simple heuristic accepting the scenario
            # that we might miss file creation (directory will be reconciled on app reset).
            # The heuristic is that we check if we have received open event for that path in the past
            # (as events may come unordered - create after open) or if we receive it before 1 second
            # after this event was received. If so, we await close event and only then call wrapper,
            # otherwise we call wrapper after 1 second passes (we assume that this was move).
            with self.sets_lock:
                self.create_paths.add(path.name)
                if path.name in self.open_paths:
                    if path.name in self.close_paths:
                        self.close_paths.remove(path.name)
                        self.open_paths.remove(path.name)
                        self.create_paths.remove(path.name)
                        # both open and close before we got create, so file is ready
                        self.wrapper._on_created(path)
                    # else was only opened, it will be dispatched by on_close
                    return
            # wasn't opened yet, add task for checker thread
            self.check_paths_queue.put(path)

        def on_opened(self, event: FileOpenedEvent):
            if event.is_directory:
                return # ignore directories
            self.open_paths.add(Path(event.src_path))

        def on_closed(self, event: FileClosedEvent):
            if event.is_directory:
                return # ignore directories
            path = Path(event.src_path)
            with self.sets_lock:
                if path.name in self.create_paths:
                    if path.name in self.open_paths:
                        self.open_paths.remove(path.name)
                    self.create_paths.remove(path.name)
                    self.wrapper._on_created(path)
                else:
                    self.close_paths.add(path.name)

        def on_moved(self, event: FileMovedEvent):
            if event.is_directory:
                return # ignore directories
            old_path = Path(event.src_path)
            if event.dest_path != '':
                new_path = Path(event.dest_path)
                self.wrapper._on_moved(old_path, new_path)

        def on_deleted(self, event: FileDeletedEvent | DirDeletedEvent):
            if event.is_directory:
                return # ignore directories
            self.wrapper._on_deleted(Path(event.src_path))

        def stop(self):
            self.check_paths_queue.put(None) # poison pill
            self.sleep_event.set() # interrupt


    def start_watcher_thread(self, loop: asyncio.AbstractEventLoop):
        self.callback_loop = loop
        self.observer = Observer()
        self.handler = self.WatchdogEventHandler(self)
        self.observer.schedule(
            self.handler,
            str(self.root_dir.absolute()),
            recursive=False,
            event_filter=[FileCreatedEvent, FileDeletedEvent, FileOpenedEvent, FileClosedEvent, FileMovedEvent]
        )
        self.observer.start()

    def _on_created(self, path: Path):
        if path.name not in self.ignored_files:
            self.callback_loop.call_soon_threadsafe(lambda: self.callback_loop.create_task(self.file_created_observer(path)))

    def _on_deleted(self, path: Path):
        if path.name not in self.ignored_files:
            self.callback_loop.call_soon_threadsafe(lambda: self.callback_loop.create_task(self.file_deleted_observer(path)))
    
    def _on_moved(self, old_path: Path, new_path: Path):
        if old_path.name not in self.ignored_files and new_path.name not in self.ignored_files:
            self.callback_loop.call_soon_threadsafe(lambda: self.callback_loop.create_task(self.file_moved_observer(old_path, new_path)))
        elif old_path.name in self.ignored_files:
            self._on_created(new_path)
        elif new_path.name in self.ignored_files:
            self._on_deleted(old_path)

    def stop(self):
        if self.observer is not None:
            self.observer.stop()
            if self.handler is not None:
                self.handler.stop()
            self.observer.join()
