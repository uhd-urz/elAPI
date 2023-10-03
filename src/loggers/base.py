import logging

from src.loggers.handlers.stderr import STDERRHandler


class MainLogger:
    def __new__(cls, suppress_stderr=False):
        from src.loggers.handlers.file import FileHandler
        from src.log_file import LOG_FILE_PATH

        logger = logging.Logger(cls.__name__)
        file_handler = FileHandler(LOG_FILE_PATH).handler
        logger.addHandler(file_handler)
        stdout_handler = STDERRHandler(suppress_stderr).handler
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        return logger


class SimpleLogger:
    def __new__(cls, suppress_stderr=False):
        logger = logging.Logger(cls.__name__)
        stdout_handler = STDERRHandler(suppress_stderr).handler
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        return logger
