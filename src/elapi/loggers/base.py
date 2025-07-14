import logging
from typing import Type, Union

from .._core_init import (
    Logger,
    LoggerUtil,
    ResultCallbackHandler,
    SimpleLogger,
    STDERRBaseHandler,
)
from .handlers.file import FileBaseHandler
from .log_file import LOG_FILE_PATH

logger_util = LoggerUtil()


@logger_util.register_wrapper_class()
class MainLogger:
    suppress: bool = False
    suppress_stderr: bool = False
    suppress_result_callback: bool = False

    def __new__(cls):
        logger = logger_util.get_registered_logger(cls.__name__)
        if logger is None:
            logger = logger_util.create_singleton_logger(name=cls.__name__)
            if not cls.suppress:
                file_handler = FileBaseHandler(LOG_FILE_PATH).handler
                logger.addHandler(file_handler)
            if not cls.suppress or not cls.suppress_stderr:
                stdout_handler = STDERRBaseHandler().handler
                logger.addHandler(stdout_handler)
            if not cls.suppress or not cls.suppress_result_callback:
                result_callback_handler = ResultCallbackHandler()
                result_callback_handler.setLevel(logging.INFO)
                logger.addHandler(result_callback_handler)
        return logger


@logger_util.register_wrapper_class()
class FileLogger:
    suppress: bool = False

    def __new__(cls):
        logger = logger_util.get_registered_logger(cls.__name__)
        if logger is None:
            if not cls.suppress:
                logger = logger_util.create_singleton_logger(name=cls.__name__)
                file_handler = FileBaseHandler(LOG_FILE_PATH).handler
                logger.addHandler(file_handler)
        return logger


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
