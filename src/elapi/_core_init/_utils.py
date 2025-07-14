from pathlib import Path
from typing import Callable, Optional

from .._names import VERSION_FILE_NAME

__all__ = [
    "NoException",
    "get_app_version",
    "GlobalCLIResultCallback",
    "PatternNotFoundError",
    "GlobalCLICallback",
    "GlobalCLIGracefulCallback",
]


class NoException(Exception): ...


class PatternNotFoundError(Exception): ...


def get_app_version() -> str:
    return Path(f"{__file__}/../../{VERSION_FILE_NAME}").resolve().read_text().strip()


class _Callback:
    _callbacks: Optional[list[Callable]] = None

    def __init__(self):
        self._callbacks: Optional[list[Callable]] = None

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
        if isinstance(func, Callable):
            if func not in self._callbacks:
                self._callbacks.append(func)
                return
        raise TypeError("result_callback function must be a callable!")

    def remove_callback(self, func: Callable) -> None:
        if isinstance(self._callbacks, list):
            self._callbacks.remove(func)
            return
        raise self._invalid_callback_type_exception()

    def call_callbacks(self) -> None:
        if self._callbacks is not None:
            if not isinstance(self._callbacks, list):
                raise self._invalid_callback_type_exception()
            for func in self._callbacks:
                if not isinstance(func, Callable):
                    raise RuntimeError(
                        f"result_callback function must be a callable! "
                        f"But '{func}' is of type '{type(func)}' instead."
                    )
                func()
            self._callbacks.clear()
            self._callbacks = None

    def get_callbacks(self) -> Optional[list[Callable]]:
        return self._callbacks


class GlobalCLIResultCallback:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = _Callback()
        return cls._instance


class GlobalCLICallback:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = _Callback()
        return cls._instance


class GlobalCLIGracefulCallback:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = _Callback()
        return cls._instance
