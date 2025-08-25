import errno
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from typing import IO, Generator, Optional, Self, Union

from ._core_init import Logger, NoException


class ProperPath:
    def __init__(
        self,
        name: Union[str, Path, None, "ProperPath"],
        env_var: bool = False,
        kind: Optional[str] = None,  # Here, None => Undefined/unknown
        err_logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.env_var = env_var
        self.kind = kind
        self.err_logger = err_logger or Logger()
        self.PathException = NoException

    def __str__(self):
        return str(self.expanded)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(name={self.name}, env_var={self.env_var}, kind={self.kind}, "
            f"err_logger={self.err_logger})"
        )

    def __eq__(self, to: Union[str, Path, "ProperPath"]):
        return self.expanded == ProperPath(to).expanded

    def __truediv__(self, other) -> "ProperPath":
        return ProperPath(self.expanded / other, err_logger=self.err_logger)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        if isinstance(
            value, ProperPath
        ):  # We want to be able to pass a ProperPath() to ProperPath()
            value = value.name
        if value == "":
            raise ValueError("Path cannot be an empty string!")
        self._name = value

    @property
    def err_logger(self):
        return self._err_logger

    @err_logger.setter
    def err_logger(self, value):
        if not isinstance(value, logging.Logger):
            raise ValueError("'err_logger' must be a logging.Logger instance!")
        self._err_logger = value

    # noinspection PyPep8Naming
    @property
    def PathException(self) -> Union[type[Exception], type[BaseException]]:
        return self._PathException

    # noinspection PyPep8Naming
    # noinspection PyAttributeOutsideInit
    @PathException.setter
    def PathException(self, value) -> None:
        if not issubclass(value, (Exception, BaseException)):
            raise ValueError(
                "Only an instance of Exception or BaseException can be "
                "assigned to descriptor PathException."
            )
        self._PathException = value

    # noinspection PyPep8Naming
    @PathException.deleter
    def PathException(self):
        raise AttributeError("PathException cannot be deleted!")

    @property
    def expanded(self) -> Path:
        if self.env_var:
            try:
                return Path(os.environ[self.name]).expanduser()
            except KeyError as e:
                raise ValueError(
                    f"Environment variable {self.name} doesn't exist."
                ) from e
        return Path(self.name).expanduser()

    @expanded.setter
    def expanded(self, value) -> None:
        raise AttributeError("Expanded is not meant to be modified.")

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, value) -> None:
        if value is None:
            self._kind = (
                "dir"
                if self.expanded.is_dir()
                else "file"
                if (
                    self.expanded.is_file()
                    or self.expanded.suffix
                    or self.expanded.exists()
                )
                # self.expanded.exists() for special files like /dev/null
                # since is_file() doesn't consider /dev/null to be a file!
                else "dir"
            )
        else:
            match value.lower():
                case "file":
                    self._kind = "file"
                case "dir" | "directory" | "folder":
                    self._kind = "dir"
                case _:
                    raise ValueError(
                        "Invalid value for parameter 'kind'. The following values "
                        "for 'kind' are allowed: file, dir."
                    )

    @staticmethod
    def _error_helper_compare_path_source(
        source: Union[Path, str], target: Union[Path, str]
    ) -> str:
        return (
            f"PATH={target} from SOURCE={source}"
            if str(source) != str(target)
            else f"PATH={target}"
        )

    def create(self, verbose: bool = True) -> None:
        path = self.expanded.resolve(strict=False)
        try:
            match self.kind:
                case "file":
                    path_parent, path_file = path.parent, path.name
                    if not path_parent.exists() and verbose:
                        self.err_logger.info(
                            f"Directory {self._error_helper_compare_path_source(self.name, path_parent)} "
                            f"could not be found. An attempt to create directory "
                            f"{path_parent} will be made."
                        )
                    path_parent.mkdir(parents=True, exist_ok=True)
                    (path_parent / path_file).touch(exist_ok=True)
                case "dir":
                    if not path.exists() and verbose:
                        self.err_logger.info(
                            f"Directory {self._error_helper_compare_path_source(self.name, path)} "
                            f"could not be found. An attempt to create directory "
                            f"{path} will be made."
                        )
                    path.mkdir(parents=True, exist_ok=True)
        except (exception := PermissionError) as e:
            message = f"Permission to create {self._error_helper_compare_path_source(self.name, path)} is denied."
            self.err_logger.error(message)
            self.PathException = exception
            raise e
        except (exception := NotADirectoryError) as e:
            # Both "file" and "dir" cases are handled, but when path is under special files like
            # /dev/null/<directory name>, os.mkdir() will throw NotADirectoryError.
            message = f"Couldn't create {self._error_helper_compare_path_source(self.name, path)}."
            self.err_logger.error(message)
            self.PathException = exception
            raise e
        except (exception := OSError) as os_err:
            # When an attempt to create a file or directory inside root (e.g., '/foo')
            # is made, OS can throw OSError with error no. 30 instead of PermissionError.
            self.err_logger.error(os_err)
            self.PathException = exception
            raise os_err

    def _remove_file(
        self, _file: Union[Path, Self, None] = None, verbose: bool = False
    ) -> None:
        file = _file or self.expanded
        if not isinstance(file, Path):
            raise ValueError(
                f"PATH={file} is empty or isn't a valid pathlib.Path instance! "
                f"Check instance attribute 'expanded'."
            )
        try:
            file.unlink()
        except (exception := FileNotFoundError) as e:
            # unlink() throws FileNotFoundError when a directory is passed as it expects files only
            self.err_logger.error(f"{e!r}")
            self.PathException = exception
            raise e
        except (exception := PermissionError) as e:
            message = (
                f"Permission to remove {self._error_helper_compare_path_source(self.name, file)} "
                f"as a file is denied."
            )
            self.err_logger.warning(message)
            self.PathException = exception
            raise e
        if verbose:
            self.err_logger.info(f"Deleted: {file}")

    def remove(self, parent_only: bool = False, verbose: bool = False) -> None:
        # removes everything (if parent_only is False) found inside a ProperPath except the parent directory of the path
        # if the ProperPath isn't a directory then it just removes the file
        if self.kind == "file":
            self._remove_file(verbose=verbose)
        elif self.kind == "dir":
            ls_ref = (
                self.expanded.glob(r"**/*")
                if not parent_only
                else self.expanded.glob(r"*.*")
            )
            for ref in ls_ref:
                match ProperPath(ref).kind:
                    case "file":
                        self._remove_file(_file=ref, verbose=verbose)
                        # Either FileNotFoundError and PermissionError occurring can mean that
                        # a dir path was passed when its kind is set as "file"
                    case "dir":
                        rmtree(ref)
                        self.err_logger.info(
                            f"Deleted directory (recursively): {ref}"
                        ) if verbose else ...
                        # rmtree deletes files and directories recursively.
                        # So in case of permission error with rmtree(ref), shutil.rmtree() might give better
                        # traceback message. I.e., which file or directory exactly

    @contextmanager
    def open(
        self,
        mode="r",
        encoding: Union[str, None] = None,
        **kwargs,
    ) -> Generator[IO, None, None]:
        path = self.expanded.resolve()
        file: Union[IO, None] = None
        try:
            # this try block doesn't yield anything yet. Here, we want to catch possible errors that occur
            # before the file is opened. E.g., FileNotFoundError
            file: IO = path.open(mode=mode, encoding=encoding, **kwargs)
        except (exception := FileNotFoundError) as e:
            message = f"File in {path} couldn't be found while trying to open it with mode '{mode}'!"
            self.err_logger.warning(message)
            self.PathException = exception
            raise e

        except (exception := PermissionError) as e:
            message = (
                f"Permission denied while trying to open file with mode '{mode}' for "
                f"{self._error_helper_compare_path_source(self.name, path)}."
            )
            self.err_logger.error(message)
            self.PathException = exception

            try:
                yield  # Without yield (yield None) Python throws RuntimeError: generator didn't yield.
                # I.e., contextmanager always expects a yield?
            except (exception := AttributeError) as attribute_err:
                # However, yielding None leads to attribute calls to None
                # (e.g., yield None -> file = None -> file.read() -> None.read()!! So we also catch that error.
                attribute_in_error = str(attribute_err).split()[-1]
                message = (
                    f"An attempt to access attribute {attribute_in_error} was made,"
                    f"but there was a problem opening the file {path}."
                )
                self.err_logger.warning(message)
                self.PathException = exception
                raise attribute_err
            else:
                raise e
        except (exception := OSError) as os_err:
            # When an attempt to create a file or directory inside root (e.g., '/foo')
            # is made, OS can throw OSError with error no. 30 instead of PermissionError.
            self.err_logger.error(os_err)
            self.PathException = exception
            raise os_err

        else:
            try:
                # Now we yield the contextmanager expected yield
                yield file
            except AttributeError as e:
                # This is useful for catching AttributeError when the file object is valid but the attributes being
                # attempted to access aren't valid/known/public.
                attribute_in_error = str(e).split()[-1]
                message = (
                    f"An attempt to access unknown/private attribute {attribute_in_error} "
                    f"of the file object {file} was made."
                )
                self.err_logger.warning(message)
                raise e
            except (exception := MemoryError) as e:
                message = (
                    f"Out of memory while trying to use mode '{mode}' with "
                    f"{self._error_helper_compare_path_source(self.name, path)}."
                )
                self.err_logger.critical(message)
                self.PathException = exception
                raise e
            except (exception := IOError) as io_err:
                # We catch "No disk space left" error which will likely be triggered during a write attempt on the file
                if io_err.errno == errno.ENOSPC:
                    message = (
                        f"Not enough disk space left while trying to use mode '{mode}' with "
                        f"{self._error_helper_compare_path_source(self.name, path)}."
                    )
                    self.err_logger.critical(message)
                    self.PathException = exception
                raise io_err
            except (exception := OSError) as os_err:
                self.err_logger.error(os_err)
                self.PathException = exception
                raise os_err
        finally:
            if file:
                try:
                    file.close()
                # This behavior was noticed during an experiment with "/dev/full" on Debian/Linux.
                # f = open("/dev/full", mode="w"); f.write("hello"); <- This won't trigger ENOSPC error yet.
                # But the error is triggered immediately after when closing with f.close()!*
                # f = open("/dev/full", mode="w");f.write("hello" * 10_000); <- Opening f again.
                # The above will trigger ENOSPC error, and will be captured by previous ENOSPC IOError exception.
                # Because of *, we again need to catch the error during close().
                except (exception := IOError) as io_err:
                    if io_err.errno == errno.ENOSPC:
                        message = (
                            f"An 'ENOSPC' error (not enough disk space left) is received while trying to"
                            f"close the file before using it with '{mode}'. Data may have been lost."
                            f"{self._error_helper_compare_path_source(self.name, path)}."
                        )
                        self.err_logger.critical(message)
                    self.PathException = exception
                    raise io_err
