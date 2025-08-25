from dataclasses import dataclass

from ...loggers import (
    LOG_FILE_PATH,
    FileBaseHandler,
    LoggerUtil,
    ResultCallbackHandler,
    STDERRBaseHandler,
    add_logging_level,
)

logger_util = LoggerUtil()


@dataclass
class _BillingLogLevels:
    success: str = 25


@dataclass
class _BillingLogLevelRichColors:
    success: str = "green"


@logger_util.register_wrapper_class()
class BillingLogger:
    suppress: bool = False
    suppress_stderr: bool = False
    suppress_result_callback: bool = False

    def __new__(cls):
        logger = logger_util.get_registered_logger(cls.__name__)
        if logger is None:
            logger = logger_util.create_singleton_logger(name=cls.__name__)
            for level_name, level_no in _BillingLogLevels().__dict__.items():
                add_logging_level(
                    level_name.upper(),
                    level_no,
                    method_name=level_name.lower(),
                    if_exists="KEEP",
                )
            if not cls.suppress:
                file_handler = FileBaseHandler(LOG_FILE_PATH).handler
                logger.addHandler(file_handler)
            if not cls.suppress or not cls.suppress_stderr:
                stdout_handler = STDERRBaseHandler(
                    rich_level_colors=_BillingLogLevelRichColors().__dict__
                ).handler
                logger.addHandler(stdout_handler)
            if not cls.suppress or not cls.suppress_result_callback:
                logger.addHandler(ResultCallbackHandler())
        return logger
