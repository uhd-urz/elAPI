import logging
from abc import ABC, abstractmethod
from collections import UserList
from logging import LogRecord


class BaseHandler(ABC):
    @abstractmethod
    def __eq__(self, other):
        if not (isinstance(other, BaseHandler) and hasattr(other, "__hash__")):
            raise AssertionError(
                f"'{other}' must be an instance of {BaseHandler.__class__} and "
                f"must have the '__hash__' attribute."
            )
        return self.__hash__() == other.__hash__()

    @abstractmethod
    def __hash__(self): ...

    @abstractmethod
    def formatter(self): ...

    @abstractmethod
    def handler(self): ...


BaseHandler.register(logging.Handler)


class LogItemList(UserList):
    def __init__(self, *records: list[LogRecord]) -> None:
        super().__init__(log_record for log_record in records)

    @property
    def _last_item(self) -> LogRecord:
        return self.__value

    @_last_item.setter
    def _last_item(self, value: LogRecord) -> None:
        if not isinstance(value, LogRecord):
            raise TypeError(
                f"{self.__class__.__name__} only accepts LogRecord as values."
            )
        self.__value = value

    def __setitem__(self, index: int, log_record: LogRecord) -> None:
        self.data[index] = self._last_item = log_record

    def append(self, log_record: LogRecord) -> None:
        self._last_item = log_record
        self.data.append(self._last_item)

    def insert(self, index, log_record: LogRecord) -> None:
        self._last_item = log_record
        self.data.insert(index, self._last_item)


class GlobalLogRecordContainer(LogItemList):
    _instance = None

    def __new__(cls) -> LogItemList:
        if cls._instance is None:
            cls._instance = LogItemList()
        return cls._instance
