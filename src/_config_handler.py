from pathlib import Path

from dynaconf import Dynaconf

from src._log_file_handler import _USER_HOME, _APP_NAME, _FALLBACK_DIR
from src._path_handler import ProperPath
from src._unsafe_api_token_handler import inspect_api_token_location
from src.loggers import logger

fallback_dir = _FALLBACK_DIR
app_name = _APP_NAME
user_home = _USER_HOME

# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# App internal data location
XDG_DATA_HOME = ProperPath("XDG_DATA_HOME", env_var=True).resolve()
APP_DATA_DIR = XDG_DATA_HOME / app_name if XDG_DATA_HOME else ProperPath(fallback_dir).resolve()
# if XDG_DATA_HOME isn't defined in the machine it falls back to fallback_dir
if not fallback_dir:
    logger.critical(f"Permission denied when trying to create fallback directory '{fallback_dir}' "
                    f"for elabftw-get internal application data. "
                    "The program may still work but this issue should be fixed.")

# API response data location
RESPONSE_CACHE_DIR = ProperPath('/var/tmp/elabftw-get').resolve()

# Download location
XDG_DOWNLOAD_DIR = ProperPath('XDG_DOWNLOAD_DIR', env_var=True).resolve()
FALLBACK_DOWNLOAD_DIR = ProperPath(user_home / 'Downloads').resolve()
DOWNLOAD_DIR = XDG_DOWNLOAD_DIR if XDG_DOWNLOAD_DIR else FALLBACK_DOWNLOAD_DIR
# Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

CONFIG_FILE_NAME = f"{app_name}.yaml"

SYSTEM_CONFIG_LOC = ProperPath("/etc").resolve() / CONFIG_FILE_NAME

# reference for the following directory conventions:
# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
XDG_CONFIG_HOME = ProperPath('XDG_CONFIG_HOME', env_var=True).resolve()
LOCAL_CONFIG_LOC = XDG_CONFIG_HOME / CONFIG_FILE_NAME if XDG_CONFIG_HOME \
    else user_home / '.config' / CONFIG_FILE_NAME
# In case, $XDG_CONFIG_HOME isn't defined in the machine, it falls back to $HOME/.config/elabftw-get.yaml

PROJECT_CONFIG_LOC = Path.cwd() / CONFIG_FILE_NAME

settings = Dynaconf(
    envar_prefix="ELABFTW_GET",
    env_switcher="ELABFTW_GET_ENV",
    # environment variable to apply mode of environment (e.g., dev, production)
    core_loaders=['YAML'],  # will not read any file extensions except YAML
    # loaders=['conf'],  # will not work without properly defining a custom loader for .conf first
    yaml_loader='safe_load',  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC]
    # the order of settings_files list is the overwrite priority order. PROJECT_CONFIG_LOC has the highest priority.
)

try:
    HOST = settings.host  # case insensitive: settings.HOST == settings.host
    API_TOKEN = settings.api_token
    # It's called API_TOKEN. Note elabftw-python uses the term api_key
    TOKEN_BEARER = settings.token_bearer
    UNSAFE_API = settings.get('unsafe_api_token_warning')
    DOWNLOAD_DIR_FROM_CONF = settings.get('data_download_dir')
    DATA_DOWNLOAD_DIR = ProperPath(DOWNLOAD_DIR_FROM_CONF).resolve() if DOWNLOAD_DIR_FROM_CONF else DOWNLOAD_DIR
except AttributeError:
    logger.critical(
        "elabftw-get.yaml configuration file couldn't be found. Are you using project-level configuration?\n"
        "Project-level configuration is discouraged for regular use, "
        "unless you are using elabftw-get from its source directory for development purpose.\n"
        "Please use user-level configuration ($XDG_CONFIG_HOME/elabftw-get.yaml)."
    )
else:

    if UNSAFE_API:
        inspect_api_token_location(settings, unsafe_path=PROJECT_CONFIG_LOC)
