import logging
from typing import Optional

from .handlers.stderr import STDERRHandler


class LogMessageTuple:
    def __init__(
        self,
        message: str,
        level: int = logging.NOTSET,
        logger: Optional[logging.Logger] = None,
        is_aggressive: bool = False,
    ):
        self.message = message
        self.level = level
        self.logger = logger
        self.is_aggressive = is_aggressive

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        if not isinstance(value, str):
            raise ValueError("Message must be a string.")
        self._message = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if not isinstance(value, int):
            raise ValueError("Level must be a logging level in integer.")
        self._level = value

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, value):
        if not isinstance(value, (logging.Logger, type(None))):
            raise TypeError(f"logger must be an instance of {logging.Logger.__name__}.")
        self._logger = value

    @property
    def is_aggressive(self):
        return self._is_aggressive

    @is_aggressive.setter
    def is_aggressive(self, value):
        if not isinstance(value, bool):
            raise TypeError("is_aggressive must be a boolean.")
        self._is_aggressive = value

    def items(self) -> tuple[str, int, Optional[logging.Logger], bool]:
        return self.message, self.level, self.logger, self.is_aggressive


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


class FileLogger:
    logger: Optional[logging.Logger] = None
    suppress: bool = False

    def __new__(cls):
        from .handlers.file import FileHandler
        from ..configuration.log_file import LOG_FILE_PATH

        if cls.logger is None:
            cls.logger = logging.Logger(cls.__name__)
            if not cls.suppress:
                file_handler = FileHandler(LOG_FILE_PATH).handler
                cls.logger.addHandler(file_handler)
            cls.logger.setLevel(logging.DEBUG)
        return cls.logger
