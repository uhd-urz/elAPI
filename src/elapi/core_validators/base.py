import sys
from abc import abstractmethod, ABC
from typing import Any


class ValidationError(Exception): ...


class Exit(BaseException):
    if (
        hasattr(sys, "ps1")
        or hasattr(sys, "ps2")
        or sys.modules.get(
            "ptpython", False
        )  # hasattr(sys, "ps1") doesn't work with ptpython.
        or sys.modules.get("bpython", False)
    ):
        SYSTEM_EXIT: bool = False
    else:
        SYSTEM_EXIT: bool = True

    def __new__(cls, *args, **kwargs):
        if cls.SYSTEM_EXIT:
            return SystemExit(*args)
        return super().__new__(cls, *args, **kwargs)  # cls == CriticalValidationError


class RuntimeValidationError(Exit, ValidationError):
    def __init__(self, *args) -> None:
        super().__init__(*args or (1,))  # default error code is always 1


class CriticalValidationError(Exit, ValidationError): ...


class Validator(ABC):
    @abstractmethod
    def validate(self): ...


class Validate:
    def __init__(self, *_typ: (Validator, ...)):
        self.typ = _typ

    def __call__(self, *args, **kwargs) -> None:
        for typ in self.typ:
            typ.validate(*args, **kwargs)

    def get(self, *args, **kwargs) -> Any:
        for typ in self.typ:
            return typ.validate(*args, **kwargs)
