from datetime import datetime
from pathlib import Path
from typing import Any, Union, Iterable, Optional

from ...loggers import Logger
from ...path import ProperPath
from ...core_validators import PathValidator, ValidationError

logger = Logger()


class Export:
    __slots__ = (
        "file_extension",
        "format_name",
        "file_name_stub",
        "_file_name",
        "_destination",
    )

    def __init__(
        self,
        destination: Union[ProperPath, Path, str],
        /,
        file_name_stub: str,
        file_extension: str,
        format_name: str,
    ):
        self.file_extension = file_extension.lower()
        self.format_name = format_name.upper()
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

    def __call__(
        self,
        data: Any,
        encoding: Optional[str] = "utf-8",
        append_only: bool = False,
        verbose: bool = False,
    ) -> None:
        mode: str = "w" if not append_only else "a"
        if isinstance(data, bytes):
            mode += "b"
            encoding = None
        with self.destination.open(mode=mode, encoding=encoding) as file:
            file.write(data)
        if verbose:
            logger.info(
                f"{self.file_name_stub} data successfully exported to {self.destination} "
                f"in {self.format_name} format."
            )


class ExportPathValidator(PathValidator):
    def __init__(
        self,
        /,
        export_path: Union[Iterable, Union[None, str, ProperPath, Path]],
        can_overwrite: bool = False,
    ):
        self.export_path = export_path
        self.can_overwrite = can_overwrite
        super().__init__(export_path)

    @property
    def can_overwrite(self) -> bool:
        return self._can_overwrite

    @can_overwrite.setter
    def can_overwrite(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("can_overwrite attribute must be a boolean!")
        self._can_overwrite = value

    def validate(self) -> ProperPath:
        from ...configuration import APP_NAME, get_active_export_dir
        from ...styles import stdin_console, NoteText

        export_dir = get_active_export_dir()
        if self.export_path is not None:
            try:
                path = ProperPath(super().validate(), err_logger=logger)
            except ValidationError:
                logger.warning(
                    f"--export path '{self.export_path}' couldn't be validated! "
                    f"{APP_NAME} will use fallback export location."
                )
            else:
                if (
                    path.kind == "file"
                    and path.expanded.exists()
                    and path.expanded not in super()._self_created_files
                    and not self.can_overwrite
                ):
                    logger.warning(
                        f"--export path '{self.export_path}' already exists! "
                        f"{APP_NAME} will use fallback export location."
                    )
                    stdin_console.print(
                        NoteText(
                            "Use '--overwrite' to force '--export' to write to an existing file.\n",
                            stem="Note",
                        )
                    )
                    return ProperPath(export_dir, err_logger=logger)
                return path
        return ProperPath(export_dir, err_logger=logger)
