import json
from dataclasses import dataclass
from pathlib import Path

from dynaconf import Dynaconf
from dynaconf.utils import inspect

from src.path import ProperPath
from src._names import (CONFIG_FILE_NAME, APP_DATA_DIR, CONFIG_HISTORY_FILE_NAME, SYSTEM_CONFIG_LOC,
                        LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC)
from src.loggers import Logger

logger = Logger()


@dataclass
class InspectConfig:
    setting_object: Dynaconf
    config_history_location: Path = APP_DATA_DIR / CONFIG_HISTORY_FILE_NAME

    @property
    def history(self) -> list[dict]:
        return inspect.get_history(self.setting_object)

    @history.setter
    def history(self, value) -> None:
        raise AttributeError("Configuration history isn't meant to modified.")

    @property
    def inspect_applied_config_files(self) -> dict:
        config_files_with_tag: dict = {
            SYSTEM_CONFIG_LOC: "ROOT LEVEL",
            LOCAL_CONFIG_LOC: "USER LEVEL",
            PROJECT_CONFIG_LOC: "PROJECT LEVEL"
        }

        applied_config_files: list = [config["identifier"] for config in self.history]
        config_files_with_tag: dict = {str(k): v for k, v in config_files_with_tag.items() if
                                       str(k) in applied_config_files}

        return config_files_with_tag

    @inspect_applied_config_files.setter
    def inspect_applied_config_files(self, value) -> None:
        raise AttributeError("Configuration history isn't meant to modified.")

    @property
    def inspect_applied_config(self) -> dict:
        applied_config = {}
        for config in self.history:
            for k, v in config["value"].items():
                config["value"][k] = v, config["identifier"]
                applied_config.update(config["value"])
        try:
            token, token_source = applied_config["API_TOKEN"]
        except KeyError:
            ...
        else:
            applied_config["API_TOKEN_MASKED"] = (f"{token[:5]}*****{token[-5:]}", token_source) \
                if token else ("''", token_source)

        try:
            host, host_source = applied_config["HOST"]
        except KeyError:
            ...
        else:
            if not host:
                applied_config["HOST"] = "''", host_source

        return applied_config

    @inspect_applied_config.setter
    def inspect_applied_config(self, value) -> None:
        raise AttributeError("Configuration history isn't meant to modified.")

    def inspect_api_token_location(self, unsafe_path: Path):
        for d in self.history:
            if Path(d["identifier"]).absolute() == unsafe_path.absolute():
                if "API_TOKEN" in d["value"]:
                    logger.warning(
                        f"api_token in project-based configuration file found. This is highly discouraged. "
                        f"The api_token is at risk of being leaked into public repositories. If you still insist, "
                        f"please make sure {CONFIG_FILE_NAME} is included in .gitignore.")

    def store(self) -> None:
        store_location = ProperPath(self.config_history_location, err_logger=logger).create()
        with store_location.open(mode="w", encoding="utf-8") as file:
            json.dump(self.inspect_applied_config, file)
        # print(f"Active configuration history is saved in {self.config_history_location}")
