import logging
from collections import UserList

from ..loggers import LogMessageTuple


class TupleList(UserList):
    def __init__(self, *tuples: list[tuple]) -> None:
        super().__init__(tuple_ for tuple_ in tuples)

    def __setitem__(self, index: int, tuple_: tuple) -> None:
        if not isinstance(tuple_, tuple):
            try:
                tuple_ = tuple(tuple_)
            except ValueError as e:
                raise ValueError(
                    f"{self.__class__.__name__} only accepts tuples as values."
                ) from e
        self.data[index] = tuple_

    def append(self, tuple_: tuple) -> None:
        if not isinstance(tuple_, tuple):
            try:
                tuple_ = tuple(tuple_)
            except ValueError as e:
                raise ValueError(
                    f"{self.__class__.__name__} only accepts tuples as values."
                ) from e
        self.data.append(tuple_)

    def insert(self, index, tuple_: tuple) -> None:
        if not isinstance(tuple_, tuple):
            try:
                tuple_ = tuple(tuple_)
            except ValueError as e:
                raise ValueError(
                    f"{self.__class__.__name__} only accepts tuples as values."
                ) from e
        self.data.insert(index, tuple_)


class _MessagesList(TupleList):
    def __init__(self) -> None:
        super().__init__()

    def __setitem__(self, index: int, tuple_: LogMessageTuple) -> None:
        if not isinstance(tuple_, LogMessageTuple):
            raise ValueError(
                f"{self.__class__.__name__} only accepts "
                f"'{LogMessageTuple.__name__}' as values."
            )
        self.data[index] = tuple_

    def append(self, tuple_: LogMessageTuple) -> None:
        if not isinstance(tuple_, LogMessageTuple):
            raise ValueError(
                f"{self.__class__.__name__} only accepts "
                f"'{LogMessageTuple.__name__}' as values."
            )
        self.data.append(tuple_)

    def insert(self, index, tuple_: LogMessageTuple) -> None:
        if not isinstance(tuple_, LogMessageTuple):
            raise ValueError(
                f"{self.__class__.__name__} only accepts "
                f"'{LogMessageTuple.__name__}' as values."
            )
        self.data.insert(index, tuple_)


class MessagesList(TupleList):
    _instance = None

    def __new__(cls) -> _MessagesList:
        if cls._instance is None:
            cls._instance = _MessagesList()
        return cls._instance


def add_message(
    message: str, level: int = logging.NOTSET, logger: type(None) = None
) -> None:
    important_messages = MessagesList()
    important_messages.append(LogMessageTuple(message, level, logger))
