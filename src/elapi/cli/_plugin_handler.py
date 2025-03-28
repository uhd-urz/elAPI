import importlib.util
import sys
from collections import namedtuple
from pathlib import Path
from typing import List, Tuple, Generator, Union, Optional

import typer

from ..configuration import get_development_mode
from ..configuration.config import (
    ROOT_INSTALLATION_DIR,
    INTERNAL_PLUGIN_DIRECTORY_NAME,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
    INTERNAL_PLUGIN_TYPER_APP_VAR_NAME,
    EXTERNAL_LOCAL_PLUGIN_DIR,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME,
)
from ..core_validators import Validator, ValidationError, Validate
from ..loggers import Logger
from ..path import ProperPath
from ..plugins import __PACKAGE_IDENTIFIER__ as plugins_sub_package_identifier
from ..utils import add_message

logger = Logger()
PluginInfo = namedtuple("PluginInfo", ["plugin_app", "path", "venv", "project_dir"])


class InternalPluginHandler:
    @property
    def plugin_locations(self) -> List[Tuple[str, Path]]:
        _paths = []
        for path in (ROOT_INSTALLATION_DIR / INTERNAL_PLUGIN_DIRECTORY_NAME).iterdir():
            if path.is_dir():
                if (path / INTERNAL_PLUGIN_TYPER_APP_FILE_NAME).exists():
                    _paths.append((path.name, path))
        return _paths

    def get_typer_apps(self) -> Generator[typer.Typer, None, None]:
        for plugin_name, path in self.plugin_locations:
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                path / INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            module.__package__ = f"{plugins_sub_package_identifier}.{plugin_name}"  # Python will find module relative to __package__ path,
            # without this module.__package__ change Python will throw an ImportError.
            spec.loader.exec_module(module)
            try:
                yield getattr(module, INTERNAL_PLUGIN_TYPER_APP_VAR_NAME)
            except AttributeError:
                yield


class ExternalPluginLocationValidator(Validator):
    def __init__(self, location: Union[str, Path, ProperPath], /):
        self.location = location

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if not isinstance(value, ProperPath):
            try:
                value = ProperPath(value)
            except ValueError as e:
                raise ValueError(
                    f"'location' attribute for class {self.__class__.__class__} "
                    f"is invalid."
                ) from e
            else:
                self._location = value.expanded

    def validate(self):
        import os
        import yaml
        from ..configuration import (
            APP_BRAND_NAME,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME,
            EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX,
            CANON_YAML_EXTENSION,
            CONFIG_FILE_EXTENSION,
        )

        _CANON_PLUGIN_METADATA_FILE_NAME: str = (
            f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX}.{CANON_YAML_EXTENSION}"
        )
        parsed_metadata: dict = {
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS: None,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH: None,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME: None,
        }

        if self.location.is_dir():
            actual_cwd = Path.cwd()
            os.chdir(self.location)
            if (
                _canon_plugin_metadata_file := (
                    self.location / _CANON_PLUGIN_METADATA_FILE_NAME
                )
            ).exists():
                import logging

                message = (
                    f"File '{_canon_plugin_metadata_file.name}' detected in location {_canon_plugin_metadata_file}. "
                    f"If it is meant to be an {APP_BRAND_NAME} plugin metadata file, "
                    f"please rename the file extension from '{CANON_YAML_EXTENSION}' "
                    f"to '{CONFIG_FILE_EXTENSION}'. "
                    f"{APP_BRAND_NAME} only supports '{CONFIG_FILE_EXTENSION}' "
                    f"as file extension for plugin metadata files."
                )
                add_message(message, logging.INFO)

            if (
                plugin_metadata_file := (
                    self.location / EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME
                )
            ).exists():
                parsed_metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] = (
                    True
                )
                with ProperPath(plugin_metadata_file).open(mode="r") as f:
                    try:
                        plugin_metadata = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        raise ValidationError(
                            f"Plugin {CANON_YAML_EXTENSION.upper()} "
                            f"metadata file {plugin_metadata_file} exists, "
                            f"but it couldn't be parsed. Exception details: {e}"
                        )
                    else:
                        try:
                            CLI_SCRIPT_PATH = plugin_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                            ]
                        except KeyError:
                            if (
                                external_local_plugin_typer_app_file := (
                                    self.location
                                    / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME
                                )
                            ).exists():
                                parsed_metadata[
                                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                                ] = external_local_plugin_typer_app_file
                        else:
                            try:
                                CLI_SCRIPT_PATH = ProperPath(CLI_SCRIPT_PATH)
                            except (TypeError, ValueError):
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH}' "
                                    f"exists in {plugin_metadata_file}, but its assigned "
                                    f"value '{CLI_SCRIPT_PATH}' is invalid."
                                )
                            else:
                                if CLI_SCRIPT_PATH.expanded.exists():
                                    parsed_metadata[
                                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                                    ] = CLI_SCRIPT_PATH.expanded.absolute()
                                else:
                                    raise ValidationError(
                                        f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH}' "
                                        f"exists in {plugin_metadata_file}, but the path "
                                        f"{CLI_SCRIPT_PATH} does not exist."
                                    )
                        try:
                            VENV_PATH = plugin_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                            ]
                        except KeyError:
                            VENV_PATH = parsed_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                            ] = None
                        else:
                            try:
                                VENV_PATH = ProperPath(VENV_PATH)
                            except (TypeError, ValueError):
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH}' "
                                    f"exists in {plugin_metadata_file}, but its assigned "
                                    f"value '{VENV_PATH}' is invalid."
                                )
                            else:
                                if VENV_PATH.expanded.exists():
                                    parsed_metadata[
                                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                                    ] = VENV_PATH.expanded.absolute()
                                else:
                                    raise ValidationError(
                                        f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH}' "
                                        f"exists in {plugin_metadata_file}, but the path "
                                        f"{VENV_PATH} does not exist."
                                    )
                        try:
                            PROJECT_PATH = plugin_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                            ]
                        except KeyError:
                            PROJECT_PATH = parsed_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                            ] = CLI_SCRIPT_PATH.expanded.parent
                        else:
                            try:
                                PROJECT_PATH = ProperPath(PROJECT_PATH)
                            except (TypeError, ValueError):
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH}' "
                                    f"exists in {plugin_metadata_file}, but its assigned "
                                    f"value '{PROJECT_PATH}' is invalid."
                                )
                            else:
                                if PROJECT_PATH.expanded.exists():
                                    parsed_metadata[
                                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                                    ] = PROJECT_PATH.expanded.absolute()
                                else:
                                    raise ValidationError(
                                        f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH}' "
                                        f"exists in {plugin_metadata_file}, but the path "
                                        f"{PROJECT_PATH} does not exist."
                                    )
                        try:
                            PLUGIN_NAME = plugin_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                            ]
                        except KeyError:
                            PLUGIN_NAME = parsed_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                            ] = self.location.name
                        else:
                            if self.location.name != PLUGIN_NAME:
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME}' "
                                    f"exists in {plugin_metadata_file}, but it must be the same "
                                    f"name as the directory name the metadata file is in."
                                )
                            parsed_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                            ] = PLUGIN_NAME
            else:
                parsed_metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] = (
                    False
                )
                if (
                    external_local_plugin_typer_app_file := (
                        self.location / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME
                    )
                ).exists():
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                    ] = external_local_plugin_typer_app_file
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                    ] = self.location
                    PLUGIN_NAME = self.location.name
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                    ] = PLUGIN_NAME
                else:
                    raise ValueError(f"{self.location} may not be a plugin directory.")
            os.chdir(actual_cwd)
        else:
            raise ValueError(f"{self.location} is not a directory.")
        return parsed_metadata


class ExternalPluginHandler:
    @staticmethod
    def get_plugin_metadata() -> Generator[Optional[dict], None, None]:
        from ..utils import add_message
        from ..configuration import EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR

        try:
            for path in sorted(
                EXTERNAL_LOCAL_PLUGIN_DIR.iterdir(), key=lambda x: str(x).lower()
            ):
                try:
                    metadata = Validate(ExternalPluginLocationValidator(path)).get()
                except ValidationError as e:
                    add_message(f"{e}")
                    continue
                except ValueError:
                    continue
                else:
                    metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR] = path
                    yield metadata
        except FileNotFoundError:
            yield None

    @staticmethod
    def load_plugin(plugin_name: str, cli_script: Path, project_dir: Path):
        spec = importlib.util.spec_from_file_location(
            plugin_name, cli_script, submodule_search_locations=[str(project_dir)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        module.__package__ = plugin_name
        # Python will find module relative to __package__ path,
        # without this module.__package__ change Python will throw an ImportError.
        spec.loader.exec_module(module)
        return module

    def get_typer_apps(self) -> Generator[Optional[PluginInfo], None, None]:
        import logging
        from ..configuration import (
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME,
            EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH,
        )
        from ._venv_state_manager import switch_venv_state

        for metadata in self.get_plugin_metadata():
            if metadata is None:
                break
            plugin_name: str = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
            ]
            cli_script: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
            ]
            plugin_root_dir: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR
            ]
            project_dir: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
            ]
            if metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] is False:
                try:
                    module = self.load_plugin(plugin_name, cli_script, project_dir)
                except (Exception, BaseException) as e:
                    if get_development_mode() is True:
                        raise e
                    message: str = (
                        f"An exception occurred while trying to load a local "
                        f"plugin '{plugin_name}' in path {cli_script}. "
                        f"Plugin '{plugin_name}' will be ignored. "
                        f'Exception details: "{e.__class__.__name__}: {e}"'
                    )
                    add_message(message, logging.WARNING)
                    yield
                else:
                    try:
                        typer_app: typer.Typer = getattr(
                            module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
                        )
                    except AttributeError:
                        yield
                    else:
                        typer_app.info.name = plugin_name
                        yield PluginInfo(
                            typer_app,
                            plugin_root_dir,
                            None,
                            project_dir,
                        )
            else:
                venv_dir: Path = metadata[
                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                ]
                if venv_dir is not None:
                    try:
                        switch_venv_state(True, venv_dir, project_dir)
                    except (ValueError, RuntimeError) as e:
                        message: str = (
                            f"An exception occurred while trying to load a local "
                            f"plugin '{plugin_name}' with virtual environment {venv_dir} "
                            f"in path {cli_script}. "
                            f"Plugin '{plugin_name}' will be ignored. "
                            f'Exception details: "{e.__class__.__name__}: {e}"'
                        )
                        add_message(message, logging.WARNING)
                        yield
                    else:
                        try:
                            module = self.load_plugin(
                                plugin_name, cli_script, project_dir
                            )
                        except (Exception, BaseException) as e:
                            if get_development_mode() is True:
                                raise e
                            message: str = (
                                f"An exception occurred while trying to load a local "
                                f"plugin '{plugin_name}' with virtual environment {venv_dir} "
                                f"in path {cli_script}. "
                                f"Plugin '{plugin_name}' will be ignored. "
                                f'Exception details: "{e.__class__.__name__}: {e}"'
                            )
                            add_message(message, logging.WARNING)
                            yield
                        else:
                            try:
                                typer_app: typer.Typer = getattr(
                                    module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
                                )
                            except AttributeError:
                                yield
                            else:
                                switch_venv_state(False, venv_dir, project_dir)
                                typer_app.info.name = plugin_name
                                yield PluginInfo(
                                    typer_app, plugin_root_dir, venv_dir, project_dir
                                )
                else:
                    try:
                        module = self.load_plugin(plugin_name, cli_script, project_dir)
                    except (Exception, BaseException) as e:
                        if get_development_mode() is True:
                            raise e
                        message: str = (
                            f"An exception occurred while trying to load a local "
                            f"plugin '{plugin_name}' in path {cli_script}. "
                            f"Plugin '{plugin_name}' will be ignored. "
                            f'Exception details: "{e.__class__.__name__}: {e}"'
                        )
                        add_message(message, logging.WARNING)
                        yield
                    else:
                        try:
                            typer_app: typer.Typer = getattr(
                                module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
                            )
                        except AttributeError:
                            yield
                        else:
                            typer_app.info.name = plugin_name
                            yield PluginInfo(
                                typer_app, plugin_root_dir, None, project_dir
                            )


internal_plugin_typer_apps = InternalPluginHandler().get_typer_apps()
external_local_plugin_typer_apps = ExternalPluginHandler().get_typer_apps()
