import errno
import os
import re
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from typing import Union, Any, TextIO

from src.loggers import SimpleLogger


class ProperPath:
    def __init__(self, name: Union[str, Path, None],
                 env_var: bool = False,
                 kind: Union[str, None] = '',
                 err_logger=SimpleLogger(),
                 ):

        self.name = name
        self.env_var = env_var
        self.kind = kind
        self.err_logger = err_logger

    def __str__(self):
        return str(self.expanded)

    def __repr__(self):
        return (f"{self.__class__.__name__}(name={self.name}, env_var={self.env_var}, kind={self.kind}, "
                f"err_logger={self.err_logger})")

    def __eq__(self, to: Union[str, Path, "ProperPath"]):
        return self.expanded == ProperPath(to).expanded

    def __truediv__(self, other) -> "ProperPath":
        return ProperPath(self.expanded / other, err_logger=self.err_logger) if self.expanded else None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        if isinstance(value, ProperPath):  # We want to be able to pass a CustomPath() to CustomPath()
            value = value.name
        if value == "":
            raise ValueError("Path cannot be an empty string!")
        self._name = value

    @property
    def err_logger(self):
        return self._err_logger

    @err_logger.setter
    def err_logger(self, value):
        import logging
        if not isinstance(value, logging.Logger):
            raise ValueError(f"'err_logger' must be a logging.Logger instance!")
        self._err_logger = value

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
                self._kind = 'dir' if self.expanded.is_dir() else 'file' if (
                        self.expanded.is_file() or self.expanded.suffix) else 'dir'
            else:
                # TODO: Python pattern matching doesn't support regex matching yet.
                if re.match(r'\bfile\b', value, flags=re.IGNORECASE):
                    self._kind = 'file'
                elif re.match(r'\bdir(ectory)?\b|\b(folder)\b', value, flags=re.IGNORECASE):
                    self._kind = 'dir'
                else:
                    raise ValueError(
                        "Invalid value for parameter 'kind'. The following values for 'kind' are allowed: file, dir.")

    @staticmethod
    def _error_helper_compare_path_source(source: Union[Path, str], target: Union[Path, str]) -> str:
        return f"PATH='{target}' from SOURCE='{source}'" if str(source) != str(target) else f"PATH='{target}'"

    def exists(self) -> Union[Path, None]:
        return self.expanded if self.expanded.exists() else None

    def create(self) -> Union[Path, None]:
        # create() returns None if a path cannot be resolved.
        path = self.expanded
        if path:
            if not (path := path.resolve(strict=False)).exists():
                # except FileNotFoundError:
                message = (f"{self._error_helper_compare_path_source(self.name, path)} could not be found. "
                           f"An attempt to create PATH={path} will be made.")
                self.err_logger.warning(message)

            try:
                if self.kind == 'file':
                    path_parent, path_file = path.parent, path.name
                    path_parent.mkdir(parents=True, exist_ok=True)
                    (path_parent / path_file).touch(exist_ok=True)
                elif self.kind == 'dir':
                    path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                message = f"Permission to create {self._error_helper_compare_path_source(self.name, path)} is denied."
                self.err_logger.critical(message)
            else:
                return path

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
            self.err_logger.warning(message)

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

    @contextmanager
    def open(self, mode="r", encoding="utf-8") -> None:
        path = self.expanded
        file: Union[TextIO, None] = None
        try:
            # this try block doesn't yield anything yet. Here, we want to catch possible errors that occur
            # before the file is opened. E.g., FileNotFoundError
            file: TextIO = path.open(mode=mode, encoding=encoding)
        except FileNotFoundError:
            message = f"File in '{path}' couldn't be found while trying to open it with mode '{mode}'!"
            self.err_logger.warning(message)
        except PermissionError:
            message = (f"Permission denied while trying to open file with mode '{mode}' for "
                       f"{self._error_helper_compare_path_source(self.name, path)}.")
            self.err_logger.critical(message)

            try:
                yield  # Without yield (yield None) Python throws RuntimeError: generator didn't yield.
                # I.e., contextmanager always expects a yield?
            except AttributeError as e:
                # However, yielding None leads to attribute calls to None
                # (e.g., yield None -> file = None -> file.read() -> None.read()!! So we also catch that error.
                attribute_in_error = str(e).split()[-1]
                message = (f"An attempt to access attribute(s) (likely the attribute {attribute_in_error}) "
                           f"of the file object was made, "
                           f"but there was a problem opening the file '{path}'. "
                           f"No further operation is possible unless file can be opened.")
                self.err_logger.warning(message)

        else:
            try:
                # Now we yield the contextmanager expected yield
                yield file
            except AttributeError:
                # This is useful for catching AttributeError when the file object is valid but the attributes accessed
                # aren't valid/known/public.
                message = (f"An attempt to access unknown/private attribute of the file object {file} was made. "
                           f"No further operation is possible.")
                self.err_logger.warning(message)
            except MemoryError:
                message = (f"Out of memory while trying to use mode '{mode}' with "
                           f"{self._error_helper_compare_path_source(self.name, path)}.")
                self.err_logger.critical(message)
            except IOError as ioe:
                # We catch "No disk space left" error which will likely trigger during a write attempt on the file
                if ioe.errno == errno.ENOSPC:
                    message = (f"Not enough disk space left while trying to use mode '{mode}' with "
                               f"{self._error_helper_compare_path_source(self.name, path)}.")
                    self.err_logger.critical(message)
        finally:
            if file:
                try:
                    file.close()
                # This is a behavior that was noticed during experimenting with "/dev/full" on Debian/Linux.
                # f = open("/dev/full", mode="w"); f.write("hello"); <- This won't trigger ENOSPC error yet!
                # But the error is triggered when trying to close: f.close(); immediately after!
                # f = open("/dev/full", mode="w");f.write("hello" * 10_000); <- Opening f again,
                # this will trigger ENOSPC error, and will be captured by previous ENOSPC IOError exception.
                # Therefore, we need to catch the error again!
                except IOError as ioe:
                    if ioe.errno == errno.ENOSPC:
                        message = (f"An 'ENOSPC' error (not enough disk space left) is received while trying to"
                                   f"close the file before using it with '{mode}'. Data may have been lost."
                                   f"{self._error_helper_compare_path_source(self.name, path)}.")
                        self.err_logger.critical(message)
