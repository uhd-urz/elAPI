import errno
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from shutil import rmtree, copyfileobj
from typing import Union, Any


class ProperPath:
    def __init__(self, name: Union[str, Path, None],
                 env_var: bool = False,
                 kind: Union[str, None] = '',
                 suppress_stderr: bool = False):

        self.name = name
        self.env_var = env_var
        self.kind = kind
        self.suppress_stderr = suppress_stderr

    def __str__(self):
        return str(self.expanded)

    def __repr__(self):
        return (f"{self.__class__.__name__}(name={self.name}, env_var={self.env_var}, kind={self.kind}, "
                f"suppress_stderr={self.suppress_stderr})")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        if value == "":
            raise ValueError("Path cannot be an empty string!")
        self._name = value

    @property
    def expanded(self) -> Path:
        if self.env_var:
            env_var_val: Union[str, None] = os.getenv(self.name)
            return Path(env_var_val).expanduser() if env_var_val else None
        else:
            return Path(self.name).expanduser() if self.name else None

    @expanded.setter
    def expanded(self, value) -> None:
        raise AttributeError("Expanded is not meant to be modified.")

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, value) -> None:
        if self.expanded:
            if not value:
                self._kind = 'file' if self.expanded.suffix else 'dir'
            else:
                # TODO: Python pattern matching doesn't support regex matching yet.
                if re.match(r'\bfile\b', value, flags=re.IGNORECASE):
                    self._kind = 'file'
                elif re.match(r'\bdir(ectory)?\b|\b(folder)\b', value, flags=re.IGNORECASE):
                    self._kind = 'dir'
                else:
                    raise ValueError(
                        "Invalid value for parameter 'kind'. The following values for 'kind' are allowed: file, dir.")

    def path_error_logger(self, message: str, level: int = logging.DEBUG) -> None:
        LOG_LEVELS = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}

        try:
            from src.loggers import logger, stdout_handler
        except ImportError:
            if not self.suppress_stderr:
                print(f"{datetime.now().isoformat(sep=' ', timespec='seconds')}:{LOG_LEVELS[level]}: {message}",
                      file=sys.stderr)
        else:
            if self.suppress_stderr:
                logger.removeHandler(stdout_handler)
            logger.log(msg=message, level=level)

    @staticmethod
    def _error_helper_compare_path_source(source: Union[Path, str], target: Union[Path, str]) -> str:
        return f"PATH={target} from SOURCE={source}" if str(source) != str(target) else f"PATH={target}"

    def create(self, allocate_amount: Union[int, None] = None) -> Union[Path, None]:
        # create() returns None if a path cannot be resolved.
        path = self.expanded
        _KB_TO_BYTE_CONVERT_VAL = 10 ** 3

        if path:
            if not (path := path.resolve(strict=False)).exists():
                # except FileNotFoundError:
                message = (f"{self._error_helper_compare_path_source(self.name, path)} could not be found. "
                           f"An attempt to create PATH={path} will be made.")
                self.path_error_logger(message, level=logging.WARNING)

            try:
                if self.kind == 'file':
                    path_parent, path_file = path.parent, path.name
                    path_parent.mkdir(parents=True, exist_ok=True)
                    (path_parent / path_file).touch(exist_ok=True)
                elif self.kind == 'dir':
                    path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                message = f"Permission to create {self._error_helper_compare_path_source(self.name, path)} is denied."
                self.path_error_logger(message, level=logging.CRITICAL)
            else:
                if allocate_amount:
                    allocate_amount: int = allocate_amount * _KB_TO_BYTE_CONVERT_VAL
                    if (file_size := path.stat().st_size) < allocate_amount:
                        extended_allocate_amount: int = allocate_amount + file_size
                        self._allocate(amount=extended_allocate_amount, unit="KB")
                return path

    def _allocate(self, amount: int, **kwargs) -> None:
        path = self.expanded

        if self.kind != 'file':
            raise TypeError(f"Only files can be allocated! {path} isn't a valid file.")

        temp_path: Path = path.parent / f"{path.name}.tmp"
        unit_name: str = kwargs.get("unit")

        try:
            with path.open(mode="rb") as src, temp_path.open(mode="wb") as alloc:
                alloc.truncate(amount)
                copyfileobj(src, alloc)
            temp_path.rename(path)
        except IOError as ioe:
            if ioe.errno == errno.ENOSPC:
                message = (f"Not enough disk space is left to be able to allocate {amount} "
                           f"{unit_name} of memory for "
                           f"{self._error_helper_compare_path_source(self.name, path)}.")
                self.path_error_logger(message, level=logging.CRITICAL)
            if ioe.errno == errno.EPERM:
                message = (f"Permission to allocate {amount} {unit_name} of memory for "
                           f"{self._error_helper_compare_path_source(self.name, path)} is denied.")
                self.path_error_logger(message, level=logging.CRITICAL)

    def _remove_file(self, _file: Path = None, **kwargs) -> None:
        file = _file if _file else self.expanded
        if not isinstance(file, Path):
            raise ValueError(f"PATH={file} is empty or isn't a valid pathlib.Path instance! "
                             f"Check instance attribute 'expanded'.")

        output_handler: Any = kwargs.get('output_handler')
        try:
            file.unlink()
        except FileNotFoundError:
            # unlink() throws FileNotFoundError when a directory is passed as it expects files only
            raise ValueError(f"{file} doesn't exist or isn't a valid file!")
        except PermissionError:
            message = f"Permission to remove {self._error_helper_compare_path_source(self.name, file)} is denied."
            self.path_error_logger(message, level=logging.WARNING)

        output_handler(f"Deleted: {file}") if output_handler else ...

    def remove(self, parent_only: bool = False, output_handler: Union[None, Any] = None) -> None:
        # removes everything (if parent_only is False) found inside a ProperPath except the parent directory of the path
        # if the ProperPath isn't a directory then it just removes the file
        if self.expanded:
            if self.kind == 'file':
                self._remove_file(output_handler=output_handler)
            elif self.kind == 'dir':
                ls_ref = self.expanded.glob(r"**/*") if not parent_only else self.expanded.glob(r"*.*")
                for ref in ls_ref:
                    try:
                        self._remove_file(_file=ref, output_handler=output_handler)
                    except ValueError:  # ValueError occurring means most likely the file is a directory
                        rmtree(ref)
                        output_handler(f"Deleted directory (recursively): {ref}") if output_handler else ...
                        # rmtree deletes files and directories recursively.
                        # So in case of permission error with rmtree(ref), shutil.rmtree() might give better
                        # traceback message. I.e., which file or directory exactly
