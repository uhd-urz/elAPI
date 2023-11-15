from datetime import datetime
from pathlib import Path
from typing import Any, Union, Iterable

from ..loggers import Logger
from ..path import ProperPath
from ..validators import PathValidator, ValidationError

logger = Logger()


class Export:
    __slots__ = ("file_extension", "file_name_stub", "_file_name", "_destination")

    def __init__(
        self,
        destination: Union[ProperPath, Path, str],
        /,
        file_name_stub: str,
        file_extension: str,
    ):
        self.file_extension = file_extension.lower()
        self.file = self.file_name_stub = file_name_stub
        self.destination = destination

    @property
    def file(self) -> str:
        return self._file_name

    @file.setter
    def file(self, value):
        date = datetime.now()
        file_name_prefix: str = f'{date.strftime("%Y-%m-%d")}_{date.strftime("%H%M%S")}'
        self._file_name = f"{file_name_prefix}_{value}.{self.file_extension}"

    @property
    def destination(self) -> ProperPath:
        return self._destination

    @destination.setter
    def destination(self, value):
        if not isinstance(value, ProperPath):
            try:
                value = ProperPath(value, err_logger=logger)
            except (TypeError, ValueError) as e:
                raise ValueError("Export path is not valid!") from e
        self._destination = value / (self.file if value.kind == "dir" else "")

    def __call__(self, data: Any, verbose: bool = False) -> None:
        with self.destination.open(mode="w", encoding="utf-8") as file:
            file.write(data)
        if verbose:
            logger.info(
                f"{self.file_name_stub} data successfully exported to {self.destination} "
                f"in {self.file_extension.upper()} format."
            )


class ExportValidator(PathValidator):
    def __init__(
        self, /, export_path: Union[Iterable, Union[None, str, ProperPath, Path]]
    ):
        self.export_path = export_path
        super().__init__(export_path)

    def validate(self) -> ProperPath:
        from ..configuration import APP_NAME, EXPORT_DIR

        if self.export_path is not None:
            try:
                return ProperPath(super().validate(), err_logger=logger)
            except ValidationError:
                logger.warning(
                    f"--export path '{self.export_path}' couldn't be validated! "
                    f"{APP_NAME} will use fallback export location."
                )
        return ProperPath(EXPORT_DIR, err_logger=logger)
