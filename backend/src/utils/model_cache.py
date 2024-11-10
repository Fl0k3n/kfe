import os
from pathlib import Path
from typing import Callable, NamedTuple, Optional, TypeVar

from utils.log import logger

MODEL_CACHE_DIR = Path(__file__).parent.parent.parent.joinpath('.model_cache')
_failed_to_init_cache_dir = False

try:
    os.mkdir(MODEL_CACHE_DIR)
except FileExistsError:
    pass
except Exception as e:
    logger.error(f'Failed to create model cache directory at {MODEL_CACHE_DIR}', exc_info=e)
    _failed_to_init_cache_dir = True

def get_cache_dir() -> Optional[str]:
    if _failed_to_init_cache_dir:
        return None
    return str(MODEL_CACHE_DIR.absolute())

class LoadCachedModelArgs(NamedTuple):
    model_path: str
    cache_dir: str
    local_files_only: bool

T = TypeVar('T')

def try_loading_cached_or_download(model_id: str, loader: Callable[[LoadCachedModelArgs], T]) -> T:
    # the goal is to let app work without internet connection, by default huggingface makes api calls
    # while loading the model even if it was cached before, this function tries to force loading from
    # cache and if it fails fallbacks to downloading the model
    valid_path = model_id.replace('/', '--')
    model_snapshots_dir = MODEL_CACHE_DIR.joinpath('models--' + valid_path).joinpath('snapshots')
    model_path = None
    attempt_loading_cached = False
    try:
        if model_snapshots_dir.exists() and model_snapshots_dir.is_dir():
            snapshots = list(os.scandir(model_snapshots_dir))
            if len(snapshots) > 0:
                model_path = model_snapshots_dir.joinpath(snapshots[0].name)
                attempt_loading_cached = True
    except:
        pass

    if attempt_loading_cached:
        try:
            return loader(LoadCachedModelArgs(model_path=str(model_path.absolute()), cache_dir=get_cache_dir(), local_files_only=True)) 
        except Exception as e:
            logger.error(f'failed to load cached model from {model_path}', exc_info=e)

    return loader(LoadCachedModelArgs(model_path=model_id, cache_dir=get_cache_dir(), local_files_only=False))
