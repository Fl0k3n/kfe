import os
from typing import Callable, NamedTuple, Optional, TypeVar

from kfe.utils.log import logger
from kfe.utils.paths import CONFIG_DIR

MODEL_CACHE_DIR = CONFIG_DIR.joinpath('model_cache')
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

def try_loading_cached_or_download(model_id: str, loader: Callable[[LoadCachedModelArgs], T], cache_dir_must_have_file: str=None) -> T:
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
                if cache_dir_must_have_file:
                    if cache_dir_must_have_file in set(os.scandir(model_path)):
                        attempt_loading_cached = True
                else:
                    attempt_loading_cached = True
    except:
        pass

    if attempt_loading_cached:
        try:
            return loader(LoadCachedModelArgs(model_path=str(model_path.absolute()), cache_dir=get_cache_dir(), local_files_only=True)) 
        except Exception as e:
            logger.error(f'failed to load cached model from {model_path}', exc_info=e)

    return loader(LoadCachedModelArgs(model_path=model_id, cache_dir=get_cache_dir(), local_files_only=False))
