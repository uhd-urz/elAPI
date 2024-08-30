import json
from pathlib import Path
from typing import Union

import yaml

from ...core_validators import Exit, Validator, Validate, ValidationError
from ...loggers import FileLogger
from ...path import ProperPath
from ...styles import print_typer_error, stdout_console, NoteText

file_logger = FileLogger()


class ValidateCLIJSONFile(Validator):
    FILE_EXTENSION: str = "json"

    def __init__(
        self, json_file_path: Union[str, ProperPath, Path], /, option_name: str
    ):
        self.json_file_path = json_file_path
        self.option_name = option_name

    @property
    def json_file_path(self) -> ProperPath:
        return self._json_file_path

    @json_file_path.setter
    def json_file_path(self, value):
        try:
            value = ProperPath(value)
        except ValueError:
            raise ValidationError(
                f"{self.option_name} was passed a string '{value}'"
                f"ending with '.{ValidateCLIJSONFile.FILE_EXTENSION}', but it could not "
                f"be understood as a path."
            )
        self._json_file_path = value

    def validate(self):
        if not self.json_file_path.expanded.exists():
            err_msg = (
                f"{self.option_name} was passed a string '{self.json_file_path}' "
                f"that was assumed as a {ValidateCLIJSONFile.FILE_EXTENSION} file path, "
                f"but it doesn't exist."
            )
            file_logger.warning(err_msg)
            raise ValidationError(err_msg)
        with self.json_file_path.open(mode="r") as f:
            try:
                data_items = json.load(f)
            except (SyntaxError, ValueError):
                err_msg = (
                    f"{self.option_name} was passed an existing "
                    f"{ValidateCLIJSONFile.FILE_EXTENSION.upper()} "
                    f"file path '{self.json_file_path}', but the file "
                    f"content caused a {ValidateCLIJSONFile.FILE_EXTENSION.upper()}"
                    f" syntax error."
                )
                file_logger.warning(err_msg)
                raise ValidationError(err_msg)
            else:
                return data_items


class ValidateCLIYAMLFile(Validator):
    FILE_EXTENSION: str = "yml"

    def __init__(
        self, yaml_file_path: Union[str, ProperPath, Path], /, option_name: str
    ):
        self.yaml_file_path = yaml_file_path
        self.option_name = option_name

    @property
    def yaml_file_path(self) -> ProperPath:
        return self._yaml_file_path

    @yaml_file_path.setter
    def yaml_file_path(self, value):
        try:
            value = ProperPath(value)
        except ValueError:
            raise ValueError(
                f"{self.option_name} was passed a string '{value}'"
                f"ending with '.{ValidateCLIYAMLFile.FILE_EXTENSION}', but it could not "
                f"be understood as a path."
            )
        self._yaml_file_path = value

    def validate(self):
        if not self.yaml_file_path.expanded.exists():
            raise ValidationError(
                f"{self.option_name} was passed a string '{self.yaml_file_path}' "
                f"that was assumed as a {ValidateCLIYAMLFile.FILE_EXTENSION.upper()} file path, "
                f"but it doesn't exist."
            )
        with self.yaml_file_path.open(mode="r") as f:
            try:
                data_items = yaml.safe_load(f)
            except yaml.YAMLError:
                raise ValidationError(
                    f"{self.option_name} was passed an existing "
                    f"{ValidateCLIYAMLFile.FILE_EXTENSION} "
                    f"file path '{self.yaml_file_path}', but the "
                    f"{ValidateCLIYAMLFile.FILE_EXTENSION.upper()} "
                    f"file content caused a {ValidateCLIYAMLFile.FILE_EXTENSION.upper()}"
                    f" syntax error."
                )
            else:
                return data_items


def get_structured_data(
    input_: str, /, option_name: str, show_note: bool = True
) -> dict:
    from ...styles.formats import JSONFormat, YAMLFormat

    SUPPORTED_INPUT_FORMAT: str = "JSON"

    def get_data_from_file():
        if input_.endswith(JSONFormat.convention):
            try:
                items = Validate(ValidateCLIJSONFile(input_, option_name)).get()
            except ValueError as e:
                print_typer_error(f"{e}")
                raise ValueError from e
            except ValidationError as e:
                print_typer_error(f"{e}")
                raise ValueError from e
            else:
                return items
        elif input_.endswith(tuple(YAMLFormat.convention)):
            try:
                items = Validate(ValidateCLIYAMLFile(input_, option_name)).get()
            except ValueError as e:
                print_typer_error(f"{e}")
                raise ValueError from e
            except ValidationError as e:
                print_typer_error(f"{e}")
                raise ValueError from e
            else:
                return items
        print_typer_error(
            f"Valid {SUPPORTED_INPUT_FORMAT.upper()} format to {option_name} was passed, "
            f"but it could not be understood as {SUPPORTED_INPUT_FORMAT.upper()} nor a file path."
        )
        if show_note:
            stdout_console.print(
                NoteText(
                    f"See --help for how to use {option_name}.",
                    stem="Note",
                )
            )
        raise ValueError

    try:
        data: dict = json.loads(input_)
    except (SyntaxError, ValueError):
        if input_.endswith((JSONFormat.convention, *YAMLFormat.convention)):
            return get_data_from_file()
        print_typer_error(
            f"{option_name} value has caused a syntax error. "
            f"It only supports {SUPPORTED_INPUT_FORMAT} syntax."
        )
        raise Exit(1)
    else:
        try:
            data.items()
        except AttributeError:
            return get_data_from_file()
        else:
            return data
