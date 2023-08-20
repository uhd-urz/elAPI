import logging

from src._log_file_handler import LOG_FILE_PATH

logger = logging.getLogger(__name__)

stdout_handler = logging.StreamHandler()
file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8')
# stdout_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go
# file_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go

stdout_log_format = logging.Formatter('%(levelname)s:%(filename)s: %(message)s')
file_log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(filename)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

stdout_handler.setFormatter(stdout_log_format)
file_handler.setFormatter(file_log_format)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)
