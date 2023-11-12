import logging
from typing import Optional

from .handlers.stderr import STDERRHandler


class MainLogger:
    logger: Optional[logging.Logger] = None
    suppress: bool = False
    suppress_stderr: bool = False

    def __new__(cls):
        from .handlers.file import FileHandler
        from ..configuration.log_file import LOG_FILE_PATH

        if cls.logger is None:
            cls.logger = logging.Logger(cls.__name__)
            if not cls.suppress:
                file_handler = FileHandler(LOG_FILE_PATH).handler
                cls.logger.addHandler(file_handler)
            stdout_handler = STDERRHandler(
                suppress=cls.suppress or cls.suppress_stderr
            ).handler
            cls.logger.addHandler(stdout_handler)
            cls.logger.setLevel(logging.DEBUG)
        return cls.logger


class SimpleLogger:
    logger: Optional[logging.Logger] = None
    suppress: bool = False

    def __new__(cls):
        if cls.logger is None:
            cls.logger = logging.Logger(cls.__name__)
            stdout_handler = STDERRHandler(suppress=cls.suppress).handler
            cls.logger.addHandler(stdout_handler)
            cls.logger.setLevel(logging.DEBUG)
        return cls.logger
