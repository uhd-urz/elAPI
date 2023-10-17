from datetime import datetime
from pathlib import Path
from typing import Any, Union

from src.configuration import EXPORT_DIR
from src.loggers import Logger
from src.path import ProperPath
from src.validators import Validate, PathValidator, ValidationError

logger = Logger()


class Export:
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
            value = ProperPath(value)
        except (TypeError, ValueError):
            self._export_path = self.default_export_path
        else:
            validate_export_path = Validate(
                PathValidator(
                    value / (self.file if value.kind == "dir" else ""),
                    err_logger=logger,
                )
            )
            try:
                self._export_path = validate_export_path.get()
            except ValidationError:
                logger.info(
                    f"Failed to write to {value}. "
                    f"Falling back to writing export data to {self.default_export_path}."
                )
                self._export_path = self.default_export_path

    @property
    def success_message(self) -> str:
        return (
            f"\n[italic blue]{self.file_name_prefix}[/italic blue] data successfully exported "
            f"to {self.export_path} in [b]{self.file_extension.upper()}[/b] format."
        )

    def __call__(self, data: Any) -> None:
        with ProperPath(self.export_path, err_logger=logger).open(
            mode="w", encoding="utf-8"
        ) as file:
            file.write(data)
