import logging
from collections import UserList
from typing import Optional

from ..loggers import DefaultLogLevels, LogMessageTuple


class TupleList(UserList):
    def __init__(self, *tuples: list[tuple]) -> None:
        super().__init__(tuple_ for tuple_ in tuples)

    @property
    def _last_item(self) -> tuple:
        return self.__value

    @_last_item.setter
    def _last_item(self, value: tuple) -> None:
        if not isinstance(value, tuple):
            try:
                value = tuple(value)
            except ValueError as e:
                raise TypeError(
                    f"{self.__class__.__name__} only accepts tuples or "
                    f"tuple-convertible iterables as values."
                ) from e
        self.__value = value

    def __setitem__(self, index: int, tuple_: tuple) -> None:
        self.data[index] = self._last_item = tuple_

    def append(self, tuple_: tuple) -> None:
        self._last_item = tuple_
        self.data.append(self._last_item)

    def insert(self, index, tuple_: tuple) -> None:
        self._last_item = tuple_
        self.data.insert(index, self._last_item)


class MessagesList(TupleList):
    _instance = None

    class _MessagesList(TupleList):
        def __init__(self) -> None:
            super().__init__()

        @property
        def _last_item(self) -> LogMessageTuple:
            return self.__value

        @_last_item.setter
        def _last_item(self, value: tuple) -> None:
            if not isinstance(value, LogMessageTuple):
                raise ValueError(
                    f"{self.__class__.__name__} only accepts "
                    f"'{LogMessageTuple.__name__}' as values."
                )
            self.__value = value

        def __setitem__(self, index: int, tuple_: LogMessageTuple) -> None:
            self.data[index] = self._last_item = tuple_

        def append(self, tuple_: LogMessageTuple) -> None:
            self._last_item = tuple_
            self.data.append(self._last_item)

        def insert(self, index, tuple_: LogMessageTuple) -> None:
            self._last_item = tuple_
            self.data.insert(index, self._last_item)

    def __new__(cls) -> _MessagesList:
        if cls._instance is None:
            cls._instance = cls._MessagesList()
        return cls._instance


def add_message(
    message: str,
    level: int = DefaultLogLevels.INFO,
    logger: Optional[logging.Logger] = None,
    is_aggressive: bool = False,
) -> None:
    important_messages = MessagesList()
    important_messages.append(LogMessageTuple(message, level, logger, is_aggressive))
