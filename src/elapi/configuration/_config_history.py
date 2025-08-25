from collections import namedtuple
from typing import Any, Union

from dynaconf import Dynaconf
from dynaconf.utils import inspect

from .._names import (
    LOCAL_CONFIG_LOC,
    PROJECT_CONFIG_LOC,
    SYSTEM_CONFIG_LOC,
)
from ..loggers import Logger

logger = Logger()

AppliedConfigIdentity = namedtuple("AppliedConfigIdentity", ["value", "source"])
FieldValueWithKey = namedtuple("FieldValueWithKey", ["key_name", "value"])


class _ConfigRules:
    @classmethod
    def get_valid_key(cls, key_name: str, /) -> str:
        if not isinstance(key_name, str):
            raise ValueError("key must be a string!")
        return key_name.upper()


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
        for config in self._history[::-1]:
            try:
                return config["value"][_ConfigRules.get_valid_key(key)]
            except KeyError:
                continue
        return default

    def patch(self, key: str, /, value: Any) -> None:
        key = _ConfigRules.get_valid_key(key)
        for config in self._history[::-1]:
            try:
                config["value"][key]
            except KeyError:
                continue
            else:
                config["value"][key] = value
                return
        raise KeyError(f"Key '{key}' couldn't be found.")

    def delete(self, key: str, /) -> None:
        key = _ConfigRules.get_valid_key(key)
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
                applied_config.update(
                    {k: AppliedConfigIdentity(v, config["identifier"])}
                )
        return applied_config

    @applied_config.setter
    def applied_config(self, value) -> None:
        raise AttributeError(
            f"{self.__class__.__name__} instance cannot modify configuration history. "
            "Use ConfigHistory to modify history."
        )


class MinimalActiveConfiguration:
    _instance = None
    _container = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinimalActiveConfiguration, cls).__new__(cls)
        return cls._instance

    @classmethod
    def __getitem__(cls, item: str) -> AppliedConfigIdentity:
        return cls._container[_ConfigRules.get_valid_key(item)]

    @classmethod
    def __setitem__(cls, key: str, value: AppliedConfigIdentity):
        cls._container[_ConfigRules.get_valid_key(key)] = value

    @classmethod
    def update(cls, value: dict):
        for k, v in value.items():
            if not isinstance(v, AppliedConfigIdentity):
                raise ValueError(
                    f"Value '{v}' for key '{k}' must be an "
                    f"instance of {AppliedConfigIdentity.__name__}."
                )
        cls._container.update(value)

    @classmethod
    def items(cls) -> dict:
        return cls._container

    @classmethod
    def get(cls, key: str, /, default: Any = None) -> Any:
        try:
            return cls.__getitem__(key)
        except KeyError:
            return default

    @classmethod
    def get_value(cls, key: str, /, default: Any = None) -> Any:
        try:
            value, source = cls.__getitem__(key)
        except KeyError:
            return default
        else:
            return value
