import sys
from abc import ABC, abstractmethod
from typing import Any, Self, Union

from .._core_init import GlobalCLIResultCallback


class ValidationError(Exception): ...


class BaseExit(BaseException, ABC): ...


class Exit(BaseExit):
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

    def __new__(cls, *args, **kwargs) -> Union[SystemExit, Self]:
        GlobalCLIResultCallback().call_callbacks()
        if cls.SYSTEM_EXIT:
            return SystemExit(*args)
        return super().__new__(cls, *args, **kwargs)  # cls == CriticalValidationError


BaseExit.register(SystemExit)


class RuntimeValidationError(Exit, ValidationError):
    def __init__(self, *args) -> None:
        super().__init__(*args or (1,))  # the default error code is always 1


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
        return None
