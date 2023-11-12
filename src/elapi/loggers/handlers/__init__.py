import logging
from abc import ABC, abstractmethod


class Handler(ABC):
    @abstractmethod
    def __eq__(self, other):
        if not (isinstance(other, Handler) and hasattr(other, "__hash__")):
            raise AssertionError(
                f"'{other}' must be an instance of {Handler.__class__} and "
                f"must have the '__hash__' attribute."
            )
        return self.__hash__() == other.__hash__()

    @abstractmethod
    def __hash__(self):
        ...

    @abstractmethod
    def formatter(self):
        ...

    @abstractmethod
    def handler(self):
        ...


Handler.register(logging.Handler)
