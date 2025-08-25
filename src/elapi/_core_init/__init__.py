__all__ = [
    "DefaultLogLevels",
    "LogMessageTuple",
    "SimpleLogger",
    "STDERRBaseHandler",
    "Logger",
    "BaseHandler",
    "LoggerUtil",
    "add_logging_level",
    "get_app_version",
    "NoException",
    "GlobalCLIResultCallback",
    "GlobalCLISuperStartupCallback",
    "ResultCallbackHandler",
    "GlobalLogRecordContainer",
    "GlobalCLIGracefulCallback",
    "LogItemList",
    "PatternNotFoundError",
]
import logging

from .._vendor import haggis
from .._vendor.haggis.logs import add_logging_level
from ._loggers import (
    BaseHandler,
    DefaultLogLevels,
    GlobalLogRecordContainer,
    Logger,
    LoggerUtil,
    LogItemList,
    LogMessageTuple,
    ResultCallbackHandler,
    SimpleLogger,
    STDERRBaseHandler,
)
from ._utils import (
    GlobalCLIGracefulCallback,
    GlobalCLIResultCallback,
    GlobalCLISuperStartupCallback,
    NoException,
    PatternNotFoundError,
    get_app_version,
)

haggis.logs.logging = logging

try:
    # Python 3.13 deprecated _acquireLock, _releaseLock
    # Based on https://github.com/celery/billiard/issues/403, commit 81cc942
    logging._acquireLock, logging._releaseLock = (
        logging._prepareFork,
        logging._afterFork,
    )
except AttributeError:
    ...
