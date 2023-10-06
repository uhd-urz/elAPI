import os
from pathlib import Path

from dynaconf import Dynaconf

from src.log_file import LOG_FILE_PATH, XDG_DATA_HOME
from src._config_history import InspectConfig
from src.validators import Validate, ValidationError, PathValidator
from src._names import (
    APP_NAME,
    XDG_DOWNLOAD_DIR,
    FALLBACK_DIR,
    FALLBACK_EXPORT_DIR,
    CONFIG_FILE_NAME,
    TMP_DIR,
    SYSTEM_CONFIG_LOC,
    PROJECT_CONFIG_LOC,
    LOCAL_CONFIG_LOC,
    LOG_DIR_ROOT,
)
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
    core_loaders=["YAML"],  # will not read any file extensions except YAML
    # loaders=['conf'],  # will not work without properly defining a custom loader for .conf first
    yaml_loader="safe_load",  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC]
    # the order of settings_files list is the overwrite priority order. PROJECT_CONFIG_LOC has the highest priority.
)

HOST: str = settings.get(
    "host"
)  # case-insensitive: settings.get("HOST") == settings.get("host")
if not HOST:
    logger.critical(
        f"'host' is empty or missing from {CONFIG_FILE_NAME} file. "
        f"Please make sure host (URL pointing to root API endpoint) is included."
    )

API_TOKEN: str = settings.get("api_token")
if not API_TOKEN:
    logger.critical(
        f"'api_token' is empty or missing from {CONFIG_FILE_NAME} file. "
        f"Please make sure api token with at least read access is included."
    )
    # Note elabftw-python uses the term "api_key" for "API_TOKEN"

records = InspectConfig(setting_object=settings)

# UNSAFE_TOKEN_WARNING falls back to True if not defined in configuration
try:
    settings["unsafe_api_token_warning"]
except KeyError:
    UNSAFE_TOKEN_WARNING: bool = True
else:
    UNSAFE_TOKEN_WARNING: bool = settings.as_bool("unsafe_api_token_warning")
    # equivalent to settings.get(<key>, cast='@bool')

if UNSAFE_TOKEN_WARNING:
    records.inspect_api_token_location(unsafe_path=PROJECT_CONFIG_LOC)

# Here, bearer term "Authorization" already follows convention, that's why it's not part of the configuration file
TOKEN_BEARER: str = "Authorization"
# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

# Export location
validate_export_dir = Validate(
    PathValidator(
        [
            settings.get("export_dir"),
            os.getenv(XDG_DOWNLOAD_DIR, os.devnull),
            FALLBACK_EXPORT_DIR,
        ],
        err_logger=logger,
    )
)
try:
    EXPORT_DIR = validate_export_dir()
except ValidationError:
    logger.critical(
        f"{APP_NAME} couldn't validate {FALLBACK_EXPORT_DIR} to store exported data. "
        f"This is a fatal error. To quickly fix this error define an export directory "
        f"with 'export_dir' in configuration file. {APP_NAME} will not run!"
    )
    raise SystemExit()
# Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

# App internal data location
if LOG_FILE_PATH.parent != LOG_DIR_ROOT:
    APP_DATA_DIR = LOG_FILE_PATH.parent
else:
    validate_app_dir = Validate(
        PathValidator([XDG_DATA_HOME, FALLBACK_DIR], err_logger=logger)
    )
    try:
        APP_DATA_DIR = validate_app_dir() / APP_NAME
    except ValidationError:
        logger.critical(
            f"{APP_NAME} couldn't validate {FALLBACK_DIR} to store {APP_NAME} internal application data. "
            f"{APP_NAME} will not run!"
        )
        raise SystemExit()

# Temporary data storage location
# elapi will dump API response data in TMP_DIR so the data can be used for debugging purposes.
TMP_DIR: Path = ProperPath(TMP_DIR, err_logger=logger).create()

# Whether to run "cleanup" command on CLI after finishing a task (when available)
CLEANUP_AFTER: bool = settings.as_bool("cleanup_after_finish")
# Default value is False if cleanup_after_finish isn't defined in the config file
