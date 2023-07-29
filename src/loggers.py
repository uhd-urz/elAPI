import logging
from pathlib import Path
from src._app_data_handler import LOG_DIR

LOG_FILE_NAME = "elabftw-get.log"

LOG_FILE_PATH = Path(LOG_DIR) / LOG_FILE_NAME
logger = logging.getLogger(__name__)

stdout_handler = logging.StreamHandler()
file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8')
# stdout_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go
# file_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go

stdout_log_format = logging.Formatter('%(levelname)s:%(filename)s: %(message)s')
file_log_format = logging.Formatter('%(levelname)s:%(asctime)s:%(filename)s: %(message)s', datefmt='%d %b %Y %H:%M:%S')

stdout_handler.setFormatter(stdout_log_format)
file_handler.setFormatter(file_log_format)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)
