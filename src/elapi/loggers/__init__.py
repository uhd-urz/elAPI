from .base import MainLogger, SimpleLogger


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
