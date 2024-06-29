import importlib.util
import sys
from collections import namedtuple
from pathlib import Path
from typing import List, Tuple, Generator

import typer

from ..configuration import get_development_mode
from ..configuration.config import (
    ROOT_INSTALLATION_DIR,
    INTERNAL_PLUGIN_DIRECTORY_NAME,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
    INTERNAL_PLUGIN_TYPER_APP_VAR_NAME,
    EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME,
    EXTERNAL_LOCAL_PLUGIN_DIR,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME,
)
from ..loggers import Logger

logger = Logger()
PLUGIN_ERROR_MESSAGES: list = []
PluginInfo = namedtuple("PluginInfo", ["plugin_app", "path"])


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
            module.__package__ = (
                f"{__package__.removesuffix(f'.{INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX}')}"
                f".{INTERNAL_PLUGIN_DIRECTORY_NAME}.{plugin_name}"
            )  # Python will find module relative to __package__ path,
            # without this module.__package__ change Python will throw an ImportError.
            spec.loader.exec_module(module)
            try:
                yield getattr(module, INTERNAL_PLUGIN_TYPER_APP_VAR_NAME)
            except AttributeError:
                yield


class ExternalPluginHandler:
    @property
    def plugin_locations(self) -> List[Tuple[str, Path]]:
        _paths = []
        for path in sorted(
            EXTERNAL_LOCAL_PLUGIN_DIR.iterdir(), key=lambda x: str(x).lower()
        ):
            if path.is_dir():
                if (path / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME).exists():
                    _paths.append((path.name, path))
        return _paths

    def get_typer_apps(self) -> Generator[typer.Typer, None, None]:
        import sys

        for plugin_name, path in self.plugin_locations:
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                cli_script_path := (path / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME),
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            module.__package__ = (
                f"{__package__.removesuffix(f'.{EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX}')}"
                f".{EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME}.{plugin_name}"
            )  # Python will find module relative to __package__ path,
            # without this module.__package__ change Python will throw an ImportError.
            if get_development_mode() is True:
                spec.loader.exec_module(module)
            else:
                try:
                    spec.loader.exec_module(module)
                except (Exception, BaseException) as e:
                    PLUGIN_ERROR_MESSAGES.append(
                        f"An exception occurred while trying to load a local "
                        f"plugin '{plugin_name}' in path {cli_script_path}. "
                        f"Plugin '{plugin_name}' will be ignored. "
                        f'Exception details: "{e.__class__.__name__}: {e}"'
                    )
                    yield
            try:
                yield PluginInfo(
                    getattr(module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME), path
                )
            except AttributeError:
                yield


internal_plugin_typer_apps = InternalPluginHandler().get_typer_apps()
external_local_plugin_typer_apps = ExternalPluginHandler().get_typer_apps()
