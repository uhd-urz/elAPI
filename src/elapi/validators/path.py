import string
from pathlib import Path
from random import choices
from typing import Union, Iterable

from ..path import ProperPath
from .base import Validator, ValidationError

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
        path: Union[Iterable[...], Union[None, str, ProperPath, Path]],
        **kwargs,
    ):
        from ..loggers import Logger

        self.path = path
        self.err_logger = kwargs.get("err_logger", Logger())
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
                with (p / self.TMP_FILE if p.kind == "dir" else p).open(
                    mode="ba+"
                ) as f:
                    f.write(
                        b"\x06"
                    )  # Throwback: \x06 is the ASCII "Acknowledge" character
                    f.seek(f.tell() - 1)
                    if (
                        not f.read(1) == b"\x06"
                    ):  # This checks for /dev/null-type special files!
                        continue  # It'd not be possible to read from those files.
                    f.seek(f.tell() - 1)
                    f.truncate()
            except COMMON_PATH_ERRORS:
                continue
            else:
                (p / self.TMP_FILE).remove() if p.kind == "dir" else ...
                return p.expanded
        raise ValidationError("Given path(s) could not be validated!")
