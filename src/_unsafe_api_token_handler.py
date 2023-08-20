from pathlib import Path
from dynaconf.utils import inspect
from src.loggers import logger
from dynaconf import Dynaconf
from src.core_names import CONFIG_FILE_NAME


def inspect_api_token_location(setting_object: Dynaconf, unsafe_path: Path):
    history = inspect.get_history(setting_object)
    for d in history:
        if Path(d["identifier"]).absolute() == unsafe_path.absolute():
            if "API_TOKEN" in d["value"]:
                logger.warning(
                    f"api_token in project-based configuration file found. This is highly discouraged. The api_token "
                    f"is at risk of being leaked into public repositories. If you still insist, please make sure "
                    f"{CONFIG_FILE_NAME} is included in .gitignore.")
