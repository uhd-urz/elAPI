import logging

from src.loggers.handlers.stderr import STDERRHandler


class SimpleLogger:
    def __new__(cls, suppress_stderr=False):
        logger = logging.Logger(cls.__name__)
        stdout_handler = STDERRHandler(suppress_stderr).handler
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        return logger
