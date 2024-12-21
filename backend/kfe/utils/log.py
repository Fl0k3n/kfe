import logging
import os
import sys
import warnings

from kfe.utils.constants import LOG_LEVEL_ENV

warnings.simplefilter(action='ignore', category=FutureWarning)

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging._nameToLevel[os.getenv(LOG_LEVEL_ENV, logging._levelToName[logging.INFO])])
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logging.getLogger('sqlalchemy').propagate = False
