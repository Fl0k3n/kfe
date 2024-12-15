import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from kfe.utils.log import logger


async def run_file_opener_subprocess(path: Path):
    proc = await asyncio.subprocess.create_subprocess_exec(
        'open', path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

async def run_native_file_explorer_subprocess(path: Path):
    if sys.platform == 'darwin':
        command = ['open', '-R', path]
    else:
        command = ['nautilus', '--select', path]
    proc = await asyncio.subprocess.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

async def run_directory_picker_and_select_path() -> tuple[Optional[Path], bool]:
    try:
        command = ['zenity', '--file-selection', '--directory', '--title=Select a directory']
        if home := os.getenv('HOME'):
            command.extend(['--filename', home])
        proc = await asyncio.subprocess.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            path = Path(stdout.decode().strip())
            if path.exists() and path.is_dir():
                return path, False
        if proc.returncode == 1 and not stderr.decode().strip():
            return None, True
        raise Exception(f'Directory picker error code: {proc.returncode}, stderr: {stderr.decode()}')
    except Exception as e:
        logger.error('Failed to select directory', exc_info=e)
    return None, False
