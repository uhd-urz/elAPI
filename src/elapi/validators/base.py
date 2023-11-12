from abc import abstractmethod, ABC
from typing import Any

import typer


class ValidationError(Exception):
    ...


class RuntimeValidationError(typer.Exit):
    def __init__(self, *args) -> None:
        super().__init__(*args or (1,))  # default error code is always 1


class CriticalValidationError(BaseException):
    SYSTEM_EXIT: bool = True

    def __new__(cls, *args, **kwargs):
        if cls.SYSTEM_EXIT:
            return SystemExit(*args)
        return super().__new__(cls, *args, **kwargs)  # cls == CriticalValidationError


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
