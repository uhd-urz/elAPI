import logging
from typing import Optional

from src.loggers.handlers.stderr import STDERRHandler


class MainLogger:
    logger: Optional[logging.Logger] = None

    def __new__(cls, suppress_stderr=False):
        from src.loggers.handlers.file import FileHandler
        from src.configuration.log_file import LOG_FILE_PATH

        if cls.logger is None:
            cls.logger = logging.Logger(cls.__name__)
            file_handler = FileHandler(LOG_FILE_PATH).handler
            cls.logger.addHandler(file_handler)
            stdout_handler = STDERRHandler(suppress_stderr).handler
            cls.logger.addHandler(stdout_handler)
            cls.logger.setLevel(logging.DEBUG)
        return cls.logger


class SimpleLogger:
    logger: Optional[logging.Logger] = None

    def __new__(cls, suppress_stderr=False):
        if cls.logger is None:
            cls.logger = logging.Logger(cls.__name__)
            stdout_handler = STDERRHandler(suppress_stderr).handler
            cls.logger.addHandler(stdout_handler)
            cls.logger.setLevel(logging.DEBUG)
        return cls.logger
