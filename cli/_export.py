from datetime import datetime
from pathlib import Path
from typing import Any, Union

from src.config import EXPORT_DIR
from src.path import ProperPath
from src.loggers import Logger

logger = Logger()


class ExportToDirectory:
    __slots__ = ("file_extension", "file_name_prefix", "_file_name", "_export_path")

    def __init__(
        self,
        directory: Union[ProperPath, Path, str],
        /,
        file_name_prefix: str,
        file_extension: str,
    ):
        self.file_extension = file_extension.lower()
        self.file = self.file_name_prefix = file_name_prefix
        self.export_path = directory

    @property
    def file(self) -> str:
        return self._file_name

    @file.setter
    def file(self, value):
        date = datetime.now()
        file_suffix: str = f'{date.strftime("%Y-%m-%d")}_{date.strftime("%H%M%S")}'
        self._file_name = f"{value}_{file_suffix}.{self.file_extension}"

    @property
    def default_export_path(self) -> Path:
        return EXPORT_DIR / self.file

    @property
    def export_path(self) -> Path:
        return self._export_path

    @export_path.setter
    def export_path(self, value):
        try:
            export_path_ = ProperPath(value, kind="dir", err_logger=logger)
        except ValueError:
            self._export_path = self.default_export_path
        else:
            self._export_path = (export_path_ / self.file).create()
            if not self._export_path:
                logger.info(
                    f"Falling back to writing export data "
                    f"to {self.default_export_path}."
                )
                self._export_path = self.default_export_path

    @property
    def success_message(self) -> str:
        return (
            f"[blue]{self.file_name_prefix}[/blue] data successfully exported to {self.export_path} "
            f"in [b]{self.file_extension.upper()}[/b] format."
        )

    def __call__(self, data: Any) -> None:
        with ProperPath(self.export_path, err_logger=logger).open(mode="w") as file:
            file.write(data)
