from pathlib import Path
from tempfile import TemporaryFile

from dynaconf import Dynaconf

from src._config_history_handler import InspectConfig
from src._log_file_handler import initial_validation
from src._names import (APP_NAME, APP_DATA_DIR, CONFIG_FILE_NAME, LOCAL_EXPORT_DIR, TMP_DIR,
                        SYSTEM_CONFIG_LOC, PROJECT_CONFIG_LOC, LOCAL_CONFIG_LOC)
from src.loggers import Logger
from src.path import ProperPath

logger = Logger()

SYSTEM_CONFIG_LOC: Path = SYSTEM_CONFIG_LOC
LOCAL_CONFIG_LOC: Path = LOCAL_CONFIG_LOC
PROJECT_CONFIG_LOC: Path = PROJECT_CONFIG_LOC

env_var_app_name = APP_NAME.upper().replace("-", "_")

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

HOST: str = settings.get('host')  # case-insensitive: settings.get("HOST") == settings.get("host")
if not HOST:
    logger.critical(f"'host' is empty or missing from {CONFIG_FILE_NAME} file. "
                    f"Please make sure host (URL pointing to root API endpoint) is included.")

API_TOKEN: str = settings.get('api_token')
if not API_TOKEN:
    logger.critical(f"'api_token' is empty or missing from {CONFIG_FILE_NAME} file. "
                    f"Please make sure api token with at least read access is included.")
    # Note elabftw-python uses the term "api_key" for "API_TOKEN"

records = InspectConfig(setting_object=settings)
# records.store()

# UNSAFE_TOKEN_WARNING falls back to True if not defined in configuration
try:
    settings['unsafe_api_token_warning']
except KeyError:
    UNSAFE_TOKEN_WARNING: bool = True
else:
    UNSAFE_TOKEN_WARNING: bool = settings.as_bool('unsafe_api_token_warning')
    # equivalent to settings.get(<key>, cast='@bool')

if UNSAFE_TOKEN_WARNING:
    records.inspect_api_token_location(unsafe_path=PROJECT_CONFIG_LOC)

# Here, bearer term "Authorization" already follows convention, that's why it's not part of the configuration file
TOKEN_BEARER: str = 'Authorization'
# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

# Export location
try:
    EXPORT_DIR_FROM_CONF: Path = ProperPath(settings["export_dir"], err_logger=logger).create()
except (KeyError, ValueError):
    EXPORT_DIR = ProperPath(LOCAL_EXPORT_DIR, err_logger=logger).create()
else:
    try:
        with TemporaryFile(prefix=".", dir=EXPORT_DIR_FROM_CONF) as f:
            ...
    except PermissionError:
        logger.warning(f"Export directory {EXPORT_DIR_FROM_CONF} from configuration file doesn't "
                       f"have proper write permission. {APP_NAME} will fallback to using "
                       f"the default download directory {LOCAL_EXPORT_DIR}.")
        EXPORT_DIR = ProperPath(LOCAL_EXPORT_DIR, err_logger=logger).create()
    else:
        EXPORT_DIR = EXPORT_DIR_FROM_CONF
if not EXPORT_DIR:
    logger.critical("No directory for exporting data could be validated! This is a fatal error. "
                    "To quickly fix this error define an export directory with 'export_dir' in configuration file. "
                    f"{APP_NAME} will not run!")
    raise SystemExit()
# Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

# App internal data location
# The following log is triggered when APP_DATA_DIR from _log_file_handler.py is invalid (returns None),
# but LOG_DIR_ROOT is valid.
# I.e., APP_DATA_DIR could still return None when the logs are stored in /var/log/elapi.
# I.e., Both APP_DATA_DIR and FALLBACK_DIR are None
# In most cases though logs and application data would share the same local directory: ~/.local/share/elapi
_proper_app_data_dir = ProperPath(APP_DATA_DIR, err_logger=logger)
if not (initial_validation.get(APP_DATA_DIR) or (APP_DATA_DIR := _proper_app_data_dir.create())):
    logger.critical(f"Permission is denied when trying to create fallback directory '{_proper_app_data_dir.name}' "
                    f"to store {APP_NAME} internal application data. {APP_NAME}'s functionalities will be limited.")

# API response data location
# Although the following has the term cache, this cache is slightly more important than most caches.
# The business logic in apps/ gracefully rely on the downloaded files in TMP_DIR to make decisions
# Therefor we use '/var/tmp/elapi' instead of '/var/cache' or 'XDG_CACHE_HOME'.
TMP_DIR: Path = ProperPath(TMP_DIR, err_logger=logger).create()

# Whether to run "cleanup" command on CLI after finishing a task (when available)
CLEANUP_AFTER: bool = settings.as_bool('cleanup_after_finish')
# Default value is False if cleanup_after_finish isn't defined in the config file
