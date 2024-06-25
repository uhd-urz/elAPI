import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple, Generator

import typer

from ..configuration.config import (
    ROOT_INSTALLATION_DIR,
    INTERNAL_PLUGIN_DIRECTORY_NAME,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
    INTERNAL_PLUGIN_TYPER_APP_VAR_NAME,
)


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


internal_plugin_typer_apps = InternalPluginHandler().get_typer_apps()
