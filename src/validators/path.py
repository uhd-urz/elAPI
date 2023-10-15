import string
from pathlib import Path
from random import choices
from typing import Union, Iterable

from src.loggers import Logger
from src.path import ProperPath
from src.validators.base import Validator, ValidationError

logger = Logger()

COMMON_PATH_ERRORS: tuple = (
    FileNotFoundError,
    PermissionError,
    MemoryError,
    IOError,
    ValueError,
    AttributeError,
)


class PathValidator(Validator):
    def __init__(
        self,
        path: Union[Iterable[...], Union[str, ProperPath, Path]],
        err_logger=logger,
    ):
        self.path = path
        self.err_logger = err_logger
        self.TMP_FILE = (
            f".tmp_{''.join(choices(string.ascii_lowercase + string.digits, k=16))}"
        )

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if not isinstance(value, (str, type(None), ProperPath, Path, Iterable)):
            raise ValueError(
                f"{value} must be an instance (or iterable of instances) of str, ProperPath, Path"
            )
        try:
            iter(value)
        except TypeError:
            self._path = (value,)
        else:
            self._path = (value,) if isinstance(value, str) else value

    def validate(self):
        for p in self.path:
            if not isinstance(p, ProperPath):
                try:
                    p = ProperPath(p, err_logger=self.err_logger)
                except (ValueError, TypeError):
                    continue
            try:
                p.create()
                with (p / self.TMP_FILE if p.kind == "dir" else p).open(mode="ba") as f:
                    f.write(b"\0")
                    f.truncate(f.tell() - 1)
            except COMMON_PATH_ERRORS:
                continue
            else:
                (p / self.TMP_FILE).remove() if p.kind == "dir" else ...
                return p.expanded
        raise ValidationError(f"Given path(s) could not be validated!")
