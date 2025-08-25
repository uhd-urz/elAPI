import string
from pathlib import Path
from random import choices
from types import NoneType
from typing import Iterable, Optional, Union

from .._core_init import Logger
from ..path import ProperPath
from .base import ValidationError, Validator


class PathValidationError(ValidationError):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.errno: Optional[int] = None
        # Unlike OSError errno here is an instance attribute instead a class attribute.
        # This will ensure broad use of errno with PathValidationError in the future.

    def __call__(self, *args):
        super().__init__(*args)
        return self


class PathValidator(Validator):
    def __init__(
        self,
        path: Union[Iterable, Union[None, str, ProperPath, Path]],
        retain_created_file: bool = True,
        **kwargs,
    ):
        self.path = path
        self.err_logger = kwargs.get("err_logger", Logger())
        self.TMP_FILE = (
            f".tmp_{''.join(choices(string.ascii_lowercase + string.digits, k=16))}"
        )
        self.retain_created_file = retain_created_file
        self.__self_created_files: list = []

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if not isinstance(value, (str, NoneType, ProperPath, Path, Iterable)):
            raise ValueError(
                f"{value} must be an instance (or iterable of instances) of str, ProperPath, Path"
            )
        try:
            iter(value)
        except TypeError:
            self._path = (value,)
        else:
            self._path = (value,) if isinstance(value, str) else value

    @property
    def _self_created_files(self):
        return self.__self_created_files

    def validate(self) -> Path:
        errno: Optional[int] = None
        _self_created_file: bool = False
        for p in self.path:
            if not isinstance(p, ProperPath):
                try:
                    p = ProperPath(p, err_logger=self.err_logger)
                except (ValueError, TypeError):
                    continue
            p_child = (
                ProperPath(p / self.TMP_FILE, kind="file", err_logger=self.err_logger)
                if p.kind == "dir"
                else p
            )
            try:
                if not p.expanded.exists():
                    p.create()
                    self._self_created_files.append(p.expanded)
                    _self_created_file = True
                with p_child.open(mode="ba+") as f:
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
            except (
                p.PathException,
                p_child.PathException,
                ValueError,
                AttributeError,
            ) as e:
                errno = getattr(e, "errno", None)
                continue
            else:
                if p.kind == "dir":
                    p_child.remove()
                if (
                    not self.retain_created_file
                    and _self_created_file
                    and p.kind == "file"
                    and p.expanded.stat().st_size == 0
                ):
                    p.remove()
                return p.expanded
        validation_error = PathValidationError()
        validation_error.errno = errno
        raise validation_error("Given path(s) could not be validated!")
