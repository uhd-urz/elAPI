import logging
from dataclasses import dataclass
from functools import update_wrapper
from types import NoneType
from typing import Optional

from .handlers.stderr import STDERRBaseHandler


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
        if not isinstance(value, (logging.Logger, NoneType)):
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


@dataclass
class DefaultLogLevels:
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG


class LoggerUtil:
    _logger_wrapper_classes: dict[str, type] = {}
    _logger_objects: dict[str, logging.Logger] = {}

    @classmethod
    def get_registered_wrapper_class(cls, name: str) -> Optional[type]:
        return cls._logger_wrapper_classes.get(name)

    @classmethod
    def get_registered_logger(cls, name: str) -> Optional[dict[str, logging.Logger]]:
        return cls._logger_objects.get(name)

    @classmethod
    def register_wrapper_class(cls):
        def decorator(logger_singleton):
            update_wrapper(wrapper=decorator, wrapped=logger_singleton)
            if cls._logger_wrapper_classes.get(logger_singleton.__name__) is None:
                cls._logger_wrapper_classes[logger_singleton.__name__] = (
                    logger_singleton
                )
            return cls._logger_wrapper_classes[logger_singleton.__name__]

        return decorator

    @classmethod
    def remove_registered_wrapper_class(cls, name: str) -> None:
        if cls._logger_wrapper_classes.get(name) is not None:
            cls._logger_wrapper_classes.pop(name)

    @classmethod
    def remove_registered_singleton_logger(cls, name: str) -> None:
        if cls._logger_objects.get(name) is not None:
            cls._logger_objects.pop(name)

    @classmethod
    def create_singleton_logger(cls, *, name: str, level: int = logging.DEBUG):
        if cls._logger_objects.get(name) is None:
            logger = logging.Logger(name)
            logger.setLevel(level)
            cls._logger_objects[name] = logger
        return cls._logger_objects[name]


logger_util = LoggerUtil()


@logger_util.register_wrapper_class()
class SimpleLogger:
    suppress: bool = False

    def __new__(cls):
        logger = logger_util.get_registered_logger(cls.__name__)
        if logger is None:
            logger = logger_util.create_singleton_logger(name=cls.__name__)
            if not cls.suppress:
                stdout_handler = STDERRBaseHandler().handler
                logger.addHandler(stdout_handler)
        return logger


class Logger:
    suppress: bool = False
    suppress_stderr: bool = False
    suppress_result_callback: bool = False

    def __new__(cls) -> logging.Logger:
        main_logger = logger_util.get_registered_wrapper_class("MainLogger")
        if main_logger is not None:
            main_logger.suppress = cls.suppress
            main_logger.suppress_stderr = cls.suppress_stderr
            main_logger.suppress_result_callback = cls.suppress_result_callback
            return main_logger()
        SimpleLogger.suppress = cls.suppress or cls.suppress_stderr
        return SimpleLogger()
