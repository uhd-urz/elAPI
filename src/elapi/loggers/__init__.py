import logging
from dataclasses import dataclass
from typing import Union, Type

from .base import LogMessageTuple  # noqa: F401
from .base import MainLogger, SimpleLogger, FileLogger  # noqa: F401


@dataclass
class _Constants:
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG


class Logger:
    suppress: bool = False
    suppress_stderr: bool = False
    CONSTANTS = _Constants()

    def __new__(cls):
        MainLogger.suppress = cls.suppress
        MainLogger.suppress_stderr = cls.suppress_stderr
        SimpleLogger.suppress = cls.suppress or cls.suppress_stderr
        try:
            return MainLogger()
        except ImportError:
            return SimpleLogger()


def update_logger_state(
    logger_obj: Type[Union[Logger, MainLogger, FileLogger, SimpleLogger]],
    /,
    *,
    suppress: bool = False,
):
    if not issubclass(logger_obj, (Logger, MainLogger, FileLogger, SimpleLogger)):
        raise TypeError(
            f"{update_logger_state.__name__} only supports "
            f"{Logger.__name__}, {MainLogger.__name__}, "
            f"{FileLogger.__name__}, and {SimpleLogger.__name__}."
        )
    if issubclass(logger_obj, Logger):
        MainLogger.logger = None
        Logger.suppress = MainLogger.suppress = suppress
    else:
        logger_obj.logger = None
        logger_obj.suppress = suppress
