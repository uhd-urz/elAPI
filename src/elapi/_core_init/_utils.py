from pathlib import Path
from typing import Callable, Optional

from .._names import VERSION_FILE_NAME

__all__ = [
    "NoException",
    "get_app_version",
    "GlobalCLIResultCallback",
    "PatternNotFoundError",
    "GlobalCLISuperStartupCallback",
    "GlobalCLIGracefulCallback",
]
from ._loggers import Logger


class NoException(Exception): ...


class PatternNotFoundError(Exception): ...


def get_app_version() -> str:
    return Path(f"{__file__}/../../{VERSION_FILE_NAME}").resolve().read_text().strip()


class _Callback:
    def __init__(self, singleton_subclass_name: str):
        self._callbacks: Optional[list[Callable]] = None
        self.singleton_subclass_name = singleton_subclass_name
        self.in_a_call = False

    def _invalid_callback_type_exception(self):
        ValueError(
            f"_result_callbacks private attribute of class "
            f"{self.__name__} was expected to be None or a list of "
            f"callables. But it is of type '{type(self._callbacks)}'."
        )

    def add_callback(self, func: Callable) -> None:
        if self._callbacks is None:
            self._callbacks = []
        if not isinstance(self._callbacks, list):
            raise self._invalid_callback_type_exception()
        if callable(func):
            if func not in self._callbacks:
                self._callbacks.append(func)
                return
            return
        raise TypeError("result_callback function must be a callable!")

    def remove_callback(self, func: Callable) -> None:
        if isinstance(self._callbacks, list):
            self._callbacks.remove(func)
            return
        raise self._invalid_callback_type_exception()

    def call_callbacks(self) -> None:
        logger = Logger()

        if not self.in_a_call:
            if self._callbacks is not None:
                if not isinstance(self._callbacks, list):
                    raise self._invalid_callback_type_exception()
                logger.debug(
                    f"Calling {self.singleton_subclass_name} registered functions: "
                    f"{', '.join(map(str, self._callbacks))}"
                )
                for func in self._callbacks:
                    if not callable(func):
                        raise RuntimeError(
                            f"result_callback function must be a callable! "
                            f"But '{func}' is of type '{type(func)}' instead."
                        )
                    self.in_a_call = True
                    func()
                self._callbacks.clear()
                self._callbacks = None
        return None

    def get_callbacks(self) -> Optional[list[Callable]]:
        return self._callbacks


# Inheriting _Callback is not necessary for GlobalCLI* singletons to work as intended.
# But the inheritance is added to make type checker mypy happy about
# class methods' availability.
# Also, super(GlobalCLI*, cls).__new__(cls) cannot be used because
# if a class has custom __new__ in its MRO, calling object.__new__()
# with more than 1 argument raises TypeError: object.__new__() takes exactly one
# argument (the type to instantiate). See details: https://stackoverflow.com/a/65862579/7696241
class GlobalCLIResultCallback(_Callback):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = _Callback(cls.__name__)
        return cls._instance


class GlobalCLISuperStartupCallback(_Callback):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = _Callback(cls.__name__)
        return cls._instance


class GlobalCLIGracefulCallback(_Callback):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = _Callback(cls.__name__)
        return cls._instance
