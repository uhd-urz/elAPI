import logging

from src._log_file_handler import LOG_FILE_PATH
from src._path_handler import ProperPath  # should be

logger = logging.getLogger(__name__)


class CustomFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        entry = self.format(record)
        path: ProperPath = ProperPath(self.baseFilename)
        with path.open(mode="a", encoding="utf-8") as log:
            log.write(entry)
            log.write("\n")


stdout_handler = logging.StreamHandler()
custom_file_handler = CustomFileHandler(LOG_FILE_PATH)

stdout_log_format = logging.Formatter('%(levelname)s:%(filename)s: %(message)s')
file_log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(filename)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

stdout_handler.setFormatter(stdout_log_format)
custom_file_handler.setFormatter(file_log_format)

stdout_handler.setLevel(logging.DEBUG)
custom_file_handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

logger.addHandler(stdout_handler)
logger.addHandler(custom_file_handler)
