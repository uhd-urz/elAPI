import sys
from pathlib import Path

from dynaconf import Dynaconf

from src._path_handler import ProperPath
from src._unsafe_api_token_handler import inspect_api_token_location
from src.core_names import (APP_NAME, FALLBACK_DIR, APP_DATA_DIR, CONFIG_FILE_NAME, _DOWNLOAD_DIR, TMP_DIR,
                            SYSTEM_CONFIG_LOC, PROJECT_CONFIG_LOC, LOCAL_CONFIG_LOC)
from src.loggers import logger

SYSTEM_CONFIG_LOC: Path = SYSTEM_CONFIG_LOC
LOCAL_CONFIG_LOC: Path = LOCAL_CONFIG_LOC
PROJECT_CONFIG_LOC: Path = PROJECT_CONFIG_LOC

env_var_app_name = APP_NAME.upper().replace("-", "_")  # elabftw-get -> ELABFTW_GET

settings = Dynaconf(
    envar_prefix=env_var_app_name,
    env_switcher=f"{env_var_app_name}_ENV",
    # environment variable to apply mode of environment (e.g., dev, production)
    core_loaders=['YAML'],  # will not read any file extensions except YAML
    # loaders=['conf'],  # will not work without properly defining a custom loader for .conf first
    yaml_loader='safe_load',  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC]
    # the order of settings_files list is the overwrite priority order. PROJECT_CONFIG_LOC has the highest priority.
)

try:
    HOST: str = settings.host  # case insensitive: settings.HOST == settings.host
except AttributeError:
    logger.critical(f"'host' is a missing from {CONFIG_FILE_NAME} file. "
                    f"Please make sure the host or URL pointing to root API endpoint is included.")
    print("Example: `host: 'https://example.de/api/v2'`", file=sys.stderr)

try:
    API_TOKEN: str = settings.api_token
except AttributeError:
    logger.critical(f"'api_token' is a missing from {CONFIG_FILE_NAME} file. "
                    f"Please make sure the an api token with at least read access is included.")
    # Note elabftw-python uses the term api_key for "API_TOKEN"
else:
    # UNSAFE_API: bool  # works but defeats the purpose of using walrus operator :/
    if UNSAFE_API := settings.get('unsafe_api_token_warning'):
        inspect_api_token_location(settings, unsafe_path=PROJECT_CONFIG_LOC)

    # Here, bearer term "Authorization" already follows convention, that's why it's not part of the configuration file
    TOKEN_BEARER: str = "Authorization"

    # Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    # Download location
    DOWNLOAD_DIR_FROM_CONF: str = settings.get('data_download_dir')
    # XDG_DOWNLOAD_DIR: Path = ProperPath('XDG_DOWNLOAD_DIR', env_var=True).resolve()
    # FALLBACK_DOWNLOAD_DIR: Path = ProperPath(user_home / 'Downloads').resolve()
    DOWNLOAD_DIR: Path = ProperPath(DOWNLOAD_DIR_FROM_CONF).resolve() if DOWNLOAD_DIR_FROM_CONF else _DOWNLOAD_DIR
    # Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

    # App internal data location
    APP_DATA_DIR: Path = APP_DATA_DIR
    # APP_DATA_DIR doesn't need to be ProperPath().resolved as it is already resolved by _log_file_handler.py
    # if XDG_DATA_HOME isn't defined in the machine it falls back to fallback_dir

    # The following log is triggered when APP_DATA_DIR from _log_file_handler.py is not set but LOG_DIR_ROOT is, and
    # at the same time FALLBACK_DIR couldn't be resolved (returns None) as well.
    # So APP_DATA_DIR could still return None when the logs are stored in /var/log/elabftw-get.
    # In most cases though logs and application data would share the same local directory: ~/.local/share/elabftw-get
    if not (APP_DATA_DIR or ProperPath(FALLBACK_DIR).resolve()):
        # equivalent to: if not APP_DATA_DIR and not ProperPath(FALLBACK_DIR).resolve(); De Morgan's law ;)
        logger.critical(f"Permission denied when trying to create fallback directory '{FALLBACK_DIR}' "
                        f"to store {APP_NAME} internal application data. "
                        "The program may still work but this issue should be fixed.")
    # APP_DATA_DIR isn't currently in use
    # However, it's meant to be utilized to store various local data

    # API response data location
    # Although the following has the term cache, this cache is slightly more important than most caches.
    # The business logic in apps/ gracefully rely on the downloaded files in TMP_DIR to make decisions
    # Therefor we use '/var/tmp/elabftw-get' instead of '/var/cache' or 'XDG_CACHE_HOME'.
    TMP_DIR: Path = ProperPath(TMP_DIR).resolve()
