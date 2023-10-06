from abc import abstractmethod, ABC
from json import JSONDecodeError
from typing import Any

from httpx import (
    UnsupportedProtocol,
    ConnectError,
    ConnectTimeout,
    InvalidURL,
)

COMMON_NETWORK_ERRORS: tuple = (
    JSONDecodeError,
    UnsupportedProtocol,
    InvalidURL,
    ConnectError,
    ConnectTimeout,
    TimeoutError,
)

COMMON_PATH_ERRORS: tuple = (
    FileNotFoundError,
    PermissionError,
    MemoryError,
    IOError,
    ValueError,
    AttributeError,
)


class ValidationError(Exception):
    ...


class Validator(ABC):
    @abstractmethod
    def validate(self):
        ...


class Validate:
    def __init__(self, *_typ: (Validator, ...)):
        self.typ = _typ

    def __call__(self, *args, **kwargs) -> None:
        for typ in self.typ:
            typ.validate(*args, **kwargs)

    def get(self, *args, **kwargs) -> Any:
        for typ in self.typ:
            return typ.validate(*args, **kwargs)
