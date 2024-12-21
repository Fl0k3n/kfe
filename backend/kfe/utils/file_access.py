import asyncio
import multiprocessing
import os
from pathlib import Path
from typing import Optional

from kfe.utils.log import logger
from kfe.utils.platform import get_home_dir_path, is_mac_os, is_windows


async def run_file_opener_subprocess(path: Path):
    if is_windows():
        proc = await asyncio.subprocess.create_subprocess_shell(
            f'start {path}',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
    else:
        proc = await asyncio.subprocess.create_subprocess_exec(
            'open', path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
    await proc.wait()

async def run_native_file_explorer_subprocess(path: Path):
    if is_windows():
        proc = await asyncio.subprocess.create_subprocess_shell(
            f'explorer /select, "{path}"',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
    else:
        if is_mac_os():
            command = ['open', '-R', path]
        else:
            command = ['nautilus', '--select', path]
        proc = await asyncio.subprocess.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
    await proc.wait()

def _run_directory_picker_and_select_path_in_subprocess(result_queue: multiprocessing.Queue, initial_dir: str):
    # this must run from the main thread and would block the event loop
    # we can run it in a separate process, giving it the main thread
    # while the process itself can run asynchronously without blocking the loop
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update_idletasks()
        directory_path = filedialog.askdirectory(initialdir=initial_dir)
        root.destroy()
        result_queue.put(directory_path)
    except:
        result_queue.put(None)

async def run_directory_picker_and_select_path() -> tuple[Optional[Path], bool]:
    def _run_subprocess_and_get_results():
        try:
            initial_dir = get_home_dir_path()
            queue = multiprocessing.Queue()
            picker_process = multiprocessing.Process(target=_run_directory_picker_and_select_path_in_subprocess, args=(queue, initial_dir)) 
            picker_process.start()
            picker_process.join()
            directory_path = queue.get() if not queue.empty() else None
            if directory_path is None:
                return None, False
            if not directory_path:
                return None, True
            path = Path(directory_path)
            if path.exists() and path.is_dir():
                return path, False
        except Exception as e:
            logger.error('Failed to select directory', exc_info=e)
        return None, False
    return await asyncio.get_running_loop().run_in_executor(None, _run_subprocess_and_get_results)
