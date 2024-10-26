import logging
import sys

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logging.getLogger('sqlalchemy').propagate = False
