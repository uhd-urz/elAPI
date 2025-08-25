import logging
from hashlib import md5
from pathlib import Path
from typing import TextIO, Union

from ...path import ProperPath
from ..._core_init import BaseHandler


class FileBaseHandler(BaseHandler):
    class CustomFileHandler(logging.FileHandler):
        def __init__(self, filename: Union[ProperPath, Path], **kwargs):
            self.file = filename
            super().__init__(str(self.file), **kwargs)

        @property
        def file(self) -> Union[Path, ProperPath]:
            return self._file

        @file.setter
        def file(self, value):
            if not isinstance(value, (ProperPath, Path)):
                raise ValueError(
                    f"{self.__class__.__name__} only supports Path and ProperPath "
                    f"instances for 'filename'!"
                )
            self._file = value

        def _open(self) -> TextIO:
            return self.file.open(mode="a", encoding="utf-8")

        def emit(self, record: logging.LogRecord) -> None:
            entry = self.format(record)
            with self._open() as log:
                log.write(entry)
                log.write("\n")

    def __init__(self, log_file_path):
        self.log_file_path: Union[Path, ProperPath, str] = log_file_path
        self.formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(filename)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def __eq__(self, other) -> bool:
        return super().__eq__(other)

    def __hash__(self) -> int:
        unique = self.formatter.__dict__.copy()
        unique.pop("_style")
        unique.update({"log_file_path": self.log_file_path})
        return int(md5(str(unique).encode("utf-8")).hexdigest(), base=16)

    @property
    def log_file_path(self) -> ProperPath:
        return self._log_file_path

    @log_file_path.setter
    def log_file_path(self, value):
        self._log_file_path = (
            ProperPath(value) if not isinstance(value, ProperPath) else value
        )

    @property
    def formatter(self) -> logging.Formatter:
        return self._formatter

    @formatter.setter
    def formatter(self, value=None):
        if not isinstance(value, logging.Formatter):
            raise ValueError("formatter must be a 'logging.Formatter' instance!")
        self._formatter = value

    @property
    def handler(self) -> logging.Handler:
        handler = FileBaseHandler.CustomFileHandler(self.log_file_path)
        handler.setFormatter(self.formatter)
        handler.setLevel(logging.INFO)
        return handler

    @handler.setter
    def handler(self, value):
        raise AttributeError("'handler' cannot be modified!")
