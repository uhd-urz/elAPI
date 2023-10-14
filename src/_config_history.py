from pathlib import Path
from typing import Any, Union

from dynaconf import Dynaconf
from dynaconf.utils import inspect

from src._names import (
    CONFIG_FILE_NAME,
    SYSTEM_CONFIG_LOC,
    LOCAL_CONFIG_LOC,
    PROJECT_CONFIG_LOC,
    KEY_API_TOKEN,
)
from src.loggers import Logger

logger = Logger()


class ConfigHistory:
    def __init__(self, setting: Dynaconf, /):
        self.setting = setting
        self._history = inspect.get_history(self.setting)

    @property
    def setting(self) -> Dynaconf:
        return self._setting

    @setting.setter
    def setting(self, value: Dynaconf):
        if not isinstance(value, Dynaconf):
            raise ValueError("settings must be a Dynaconf instance!")
        self._setting = value

    def get(self, key: str, /, default: Any = None) -> Any:
        _item = None
        for config in self._history:
            try:
                _item = config["value"][key]
            except KeyError:
                continue
        return _item or default

    def patch(self, key: str, /, value: Any) -> None:
        _item = None
        for config in self._history:
            try:
                _item = config["value"][key] = value
            except KeyError:
                continue
        if not _item:
            raise KeyError(f"Key '{key}' couldn't be found.")

    def delete(self, key: str, /) -> None:
        _item = None
        for config in self._history:
            try:
                _item = config["value"].pop(key)
            except KeyError:
                continue
        if not _item:
            raise KeyError(f"Key '{key}' couldn't be found.")

    def items(self):
        return self._history


class InspectConfigHistory:
    def __init__(self, history_obj: Union[ConfigHistory, Dynaconf], /):
        self.history = history_obj

    @property
    def history(self) -> list[dict]:
        return self._history

    @history.setter
    def history(self, value) -> None:
        if not isinstance(value, (ConfigHistory, Dynaconf)):
            raise ValueError(
                f"{self.__class__.__name__} only accepts instance of ConfigHistory or Dynaconf."
            )
        self._history = (
            value.items()
            if isinstance(value, ConfigHistory)
            else inspect.get_history(value)
        )

    @property
    def applied_config_files(self) -> dict:
        config_files_with_tag: dict = {
            SYSTEM_CONFIG_LOC: "ROOT LEVEL",
            LOCAL_CONFIG_LOC: "USER LEVEL",
            PROJECT_CONFIG_LOC: "PROJECT LEVEL",
        }

        applied_config_files: list = [config["identifier"] for config in self.history]
        return {
            str(k): v
            for k, v in config_files_with_tag.items()
            if str(k) in applied_config_files
        }

    @applied_config_files.setter
    def applied_config_files(self, value) -> None:
        raise AttributeError(
            f"{self.__class__.__name__} instance cannot modify configuration history. "
            "Use ConfigHistory to modify history."
        )

    @property
    def applied_config(self) -> dict:
        applied_config = {}
        for config in self.history:
            for k, v in config["value"].items():
                applied_config.update({k: (v, config["identifier"])})
        return applied_config

    @applied_config.setter
    def applied_config(self, value) -> None:
        raise AttributeError(
            f"{self.__class__.__name__} instance cannot modify configuration history. "
            "Use ConfigHistory to modify history."
        )

    def inspect_api_token_location(self, unsafe_path: Path):
        for d in self.history:
            if Path(d["identifier"]).absolute() == unsafe_path.absolute():
                if KEY_API_TOKEN in d["value"]:
                    logger.warning(
                        f"api_token in project-based configuration file found. This is highly discouraged. "
                        f"The api_token is at risk of being leaked into public repositories. If you still insist, "
                        f"please make sure {CONFIG_FILE_NAME} is included in .gitignore."
                    )
