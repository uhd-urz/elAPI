from dynaconf import Dynaconf
import os
from pathlib import Path
from src.loggers import logger
from src._unsafe_api_token_handler import inspect_api_token_location

CONFIG_FILE_NAME = "elabftw-get.yaml"

SYSTEM_CONFIG_LOC = Path("/etc") / Path(f"{CONFIG_FILE_NAME}")

# reference for the following directory conventions:
# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
LOCAL_CONFIG_DIR = os.getenv('XDG_CONFIG_HOME')
CONV_CONFIG_DIR = os.getenv('HOME') + '/.config'  # In case, $XDG_CONFIG_HOME isn't defined in the machine
ASSUMED_LOCAL_CONFIG_LOC = Path(LOCAL_CONFIG_DIR) / CONFIG_FILE_NAME if LOCAL_CONFIG_DIR else (
        Path(CONV_CONFIG_DIR) / CONFIG_FILE_NAME)

PROJECT_CONFIG_LOC = Path.cwd().parent / Path(f"{CONFIG_FILE_NAME}")

settings = Dynaconf(
    envar_prefix="ELABFTW-GET",
    env_switcher="ELABFTW-GET_ENV",
    # environment variable to apply mode of environment (e.g., dev, production)
    core_loaders=['YAML'],  # will not read any file extensions except YAML
    # loaders=['conf'],  # will not work without properly defining a custom loader for .conf first
    yaml_loader='safe_load',  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, ASSUMED_LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC]
    # the order of settings_files list is the overwrite priority order
)

try:
    HOST = settings.host  # case insensitive: settings.HOST == settings.host
    API_TOKEN = settings.api_token
    # It's called API_TOKEN. Note elabftw-python uses the term api_key
    TOKEN_BEARER = settings.token_bearer
    UNSAFE_API = settings.get('unsafe_api_token_warning')
    DATA_DOWNLOAD_DIR = Path(settings.get('data_download_dir')).expanduser().resolve()
except AttributeError:
    logger.critical(
        f"elabftw-get.yaml configuration file couldn't be found. Are you using project-level configuration?\n"
        f"Project-level configuration is discouraged for regular use, "
        f"unless you are using elabftw-get from its source directory for development purpose.\n"
        f"Please use user-level configuration ($XDG_CONFIG_HOME/elabftw-get.yaml)."
    )
else:

    if UNSAFE_API:
        inspect_api_token_location(settings, unsafe_path=PROJECT_CONFIG_LOC)
