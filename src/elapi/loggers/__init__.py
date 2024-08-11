from typing import Union

from .base import LogMessageTuple  # noqa: F401
from .base import MainLogger, SimpleLogger, FileLogger  # noqa: F401


class Logger:
    suppress: bool = False
    suppress_stderr: bool = False

    def __new__(cls):
        MainLogger.suppress = cls.suppress
        MainLogger.suppress_stderr = cls.suppress_stderr
        SimpleLogger.suppress = cls.suppress or cls.suppress_stderr
        try:
            return MainLogger()
        except ImportError:
            return SimpleLogger()


def change_logger_state(
    logger_obj: Union[Logger, MainLogger, FileLogger, SimpleLogger],
    /,
    *,
    suppress: bool,
):
    if not issubclass(type(logger_obj), (Logger, MainLogger, FileLogger, SimpleLogger)):
        raise TypeError(
            f"{change_logger_state.__name__} only supports"
            f"{Logger.__name__}, {MainLogger.__name__}, "
            f"{FileLogger.__name__}, and {SimpleLogger.__name__}."
        )
    logger_obj.logger = None
    logger_obj.suppress = suppress
