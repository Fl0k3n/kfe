import os
from pathlib import Path

from kfe.utils.log import logger
from kfe.utils.platform import get_home_dir_path

_utils_path = Path(__file__).parent
CONFIG_DIR = _utils_path
try:
    if (home := get_home_dir_path()) is not None:
        home_dir = Path(home).joinpath('.kfe')
        CONFIG_DIR = home_dir
        try:
            os.mkdir(home_dir)
        except FileExistsError:
            pass
        except Exception as e:
            logger.error(f'Failed to create config directory at: {home_dir}', exc_info=e)
            CONFIG_DIR = _utils_path
except:
    pass
