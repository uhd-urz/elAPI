from src.loggers.base import MainLogger, SimpleLogger


class Logger:
    def __new__(cls, suppress_stderr: bool = False):
        try:
            return MainLogger(suppress_stderr)
        except ImportError:
            return SimpleLogger(suppress_stderr)
