import re
from collections.abc import Iterable
from typing import Optional, Literal, Type

import typer
from click import Context
from typer.core import TyperGroup

from ...configuration import APP_NAME, DEFAULT_EXPORT_DATA_FORMAT
from ...loggers import Logger
from ...path import ProperPath
from ...core_validators import Exit

logger = Logger()


class CLIExport:
    def __new__(
        cls,
        data_format: Optional[str] = None,
        export_dest: Optional[str] = None,
        can_overwrite: bool = False,
    ):
        from collections import namedtuple
        from ...core_validators import Validate
        from .export import ExportPathValidator

        try:
            validate_export = Validate(
                ExportPathValidator(export_dest, can_overwrite=can_overwrite)
            )
        except ValueError as e:
            logger.error(e)
            raise Exit(1)
        export_dest: ProperPath = validate_export.get()

        _export_file_ext: str = (
            export_dest.expanded.suffix.removeprefix(".")
            if export_dest.kind == "file"
            else None
        )
        data_format = (
            data_format or _export_file_ext or DEFAULT_EXPORT_DATA_FORMAT
        )  # default data_format format
        ExportParams = namedtuple(
            "ExportParams", ["data_format", "destination", "extension"]
        )
        return ExportParams(data_format, export_dest, _export_file_ext)


class CLIFormat:
    FALLBACK_DATA_FORMAT = DEFAULT_EXPORT_DATA_FORMAT

    def __new__(
        cls,
        data_format: str,
        export_file_ext: Optional[str] = None,
    ):
        from ...styles import Format, FormatError

        try:
            format = Format(data_format)
        except FormatError as e:
            logger.error(e)
            logger.info(
                f"{APP_NAME} will fallback to '{cls.FALLBACK_DATA_FORMAT}' format."
            )
            format = Format(
                cls.FALLBACK_DATA_FORMAT
            )  # Falls back to DEFAULT_EXPORT_DATA_FORMAT
        if export_file_ext and export_file_ext not in format.convention:
            logger.info(
                f"File extension is '{export_file_ext}' but data format will be '{format.name.upper()}'."
            )
        if isinstance(format.convention, str):
            ...
        elif isinstance(format.convention, Iterable):
            format.convention = next(iter(format.convention))
        return format


class OrderedCommands(TyperGroup):
    """
    OrderedCommands is passed to typer.Typer app so that the list of the commands on the terminal
    is shown in the order they are defined on the script instead of being shown alphabetically.
    See: https://github.com/tiangolo/typer/issues/428#issuecomment-1238866548
    """

    def list_commands(self, ctx: Context) -> Iterable[str]:
        return self.commands.keys()


class Typer(typer.Typer):
    def __new__(
        cls,
        rich_markup_mode: Literal["markdown", "rich"] = "markdown",
        cls_: Optional[Type[TyperGroup]] = OrderedCommands,
        **kwargs,
    ):
        try:
            return typer.Typer(
                pretty_exceptions_show_locals=False,
                no_args_is_help=True,
                rich_markup_mode=rich_markup_mode,
                cls=cls_,
                **kwargs,
            )
        except TypeError as e:
            if re.search(
                r"got multiple values for keyword argument",
                error_verbose := str(e),
                re.IGNORECASE,
            ):
                _reserved_key_end = re.match(
                    r"^'\w+'", error_verbose[::-1], re.IGNORECASE
                ).end()
                raise AttributeError(
                    f"{APP_NAME} overloaded class '{__package__}.{Typer.__name__}' reserves the keyword argument "
                    f"'{error_verbose[- _reserved_key_end + 1: - 1]}' for {typer.Typer.__name__} class."
                ) from e
            raise e
