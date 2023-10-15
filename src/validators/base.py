from abc import abstractmethod, ABC
from typing import Any


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
