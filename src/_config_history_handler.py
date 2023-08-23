import json
from dataclasses import dataclass
from pathlib import Path

from dynaconf import Dynaconf
from dynaconf.utils import inspect

from src._path_handler import ProperPath
from src.core_names import CONFIG_FILE_NAME, APP_DATA_DIR, CONFIG_HISTORY_FILE_NAME
from src.loggers import logger


@dataclass
class InspectConfig:
    setting_object: Dynaconf
    config_history_location: Path = APP_DATA_DIR / CONFIG_HISTORY_FILE_NAME

    @property
    def history(self):
        return inspect.get_history(self.setting_object)

    @history.setter
    def history(self, value):
        raise AttributeError("Configuration history isn't meant to modified.")

    @property
    def inspect_applied_config_files(self):
        applied_config_files: list = []
        for config in self.history:
            applied_config_files.append(config["identifier"])
        return applied_config_files

    @inspect_applied_config_files.setter
    def inspect_applied_config_files(self, value):
        raise AttributeError("Configuration history isn't meant to modified.")

    @property
    def inspect_applied_config(self):
        applied_config = {}
        for config in self.history:
            for k, v in config["value"].items():
                config["value"][k] = v, config["identifier"]
                applied_config.update(config["value"])

        token, token_source = applied_config["API_TOKEN"]
        applied_config["API_TOKEN_MASKED"] = f"{token[:5]}*****{token[-5:]}", token_source

        return applied_config

    @inspect_applied_config.setter
    def inspect_applied_config(self, value):
        raise AttributeError("Configuration history isn't meant to modified.")

    def inspect_api_token_location(self, unsafe_path: Path):
        for d in self.history:
            if Path(d["identifier"]).absolute() == unsafe_path.absolute():
                if "API_TOKEN" in d["value"]:
                    logger.warning(
                        f"api_token in project-based configuration file found. This is highly discouraged. "
                        f"The api_token is at risk of being leaked into public repositories. If you still insist, "
                        f"please make sure {CONFIG_FILE_NAME} is included in .gitignore.")

    def store(self):
        store_location = ProperPath(self.config_history_location).create()
        with store_location.open(mode="w", encoding="utf-8") as file:
            json.dump(self.inspect_applied_config, file)
        # print(f"Active configuration history is saved in {self.config_history_location}")
