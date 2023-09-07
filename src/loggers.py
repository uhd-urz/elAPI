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


stdout_handler = logging.StreamHandler()
# stdout_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go
# file_handler.setLevel(logging.ERROR)  # no default level is set so the levels can be set on the go
custom_file_handler = CustomFileHandler(LOG_FILE_PATH)

stdout_log_format = logging.Formatter('%(levelname)s:%(filename)s: %(message)s')
file_log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(filename)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

stdout_handler.setFormatter(stdout_log_format)
custom_file_handler.setFormatter(file_log_format)

logger.addHandler(stdout_handler)
logger.addHandler(custom_file_handler)
