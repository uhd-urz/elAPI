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
