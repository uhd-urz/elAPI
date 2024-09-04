import logging
import os
from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf

from ._config_history import (
    ConfigHistory,
    InspectConfigHistory,
    AppliedConfigIdentity,
    MinimalActiveConfiguration,
)
from .log_file import LOG_FILE_PATH, _XDG_DATA_HOME
# noinspection PyUnresolvedReferences
from .._names import (
    APP_NAME,
    APP_BRAND_NAME,  # noqa: F401
    CONFIG_FILE_EXTENSION,  # noqa: F401
    DEFAULT_EXPORT_DATA_FORMAT,  # noqa: F401
    VERSION_FILE_NAME,  # noqa: F401
    ELAB_NAME,  # noqa: F401
    ELAB_BRAND_NAME,  # noqa: F401
    ELAB_API_EXPECTED_VERSION,  # noqa: F401
    ELAB_HOST_URL_API_SUFFIX,  # noqa: F401
    ENV_XDG_DOWNLOAD_DIR,
    FALLBACK_DIR,
    FALLBACK_EXPORT_DIR,  # noqa: F401
    CONFIG_FILE_NAME,  # noqa: F401
    TMP_DIR,
    SYSTEM_CONFIG_LOC,
    PROJECT_CONFIG_LOC,
    LOCAL_CONFIG_LOC,
    LOG_DIR_ROOT,
    KEY_HOST,
    KEY_API_TOKEN,
    KEY_EXPORT_DIR,
    KEY_UNSAFE_TOKEN_WARNING,
    KEY_ENABLE_HTTP2,
    KEY_VERIFY_SSL,
    KEY_TIMEOUT,
    KEY_DEVELOPMENT_MODE,
    KEY_PLUGIN_KEY_NAME,
)
from ..core_validators import (
    Validate,
    ValidationError,
    CriticalValidationError,
    PathValidator,
)
from ..loggers import Logger
from ..path import ProperPath
from ..styles import Missing
from ..utils import add_message

logger = Logger()

SYSTEM_CONFIG_LOC: Path = SYSTEM_CONFIG_LOC
LOCAL_CONFIG_LOC: Path = LOCAL_CONFIG_LOC
PROJECT_CONFIG_LOC: Path = PROJECT_CONFIG_LOC

env_var_app_name = APP_NAME.upper().replace("-", "_")
FALLBACK_SOURCE_NAME: str = "DEFAULT"

CANON_YAML_EXTENSION: str = "yaml"
_CANON_CONFIG_FILE_NAME: str = f"{APP_NAME}.{CANON_YAML_EXTENSION}"
CONFIG_MIS_PATH: Optional[Path] = None
for path in [
    SYSTEM_CONFIG_LOC.parent / _CANON_CONFIG_FILE_NAME,
    LOCAL_CONFIG_LOC.parent / _CANON_CONFIG_FILE_NAME,
    PROJECT_CONFIG_LOC.parent / _CANON_CONFIG_FILE_NAME,
]:
    if path.exists():
        CONFIG_MIS_PATH = path
        message = (
            f"You have a message marked as 'Attention' waiting for you. "
            f"Please run '{APP_NAME} show-config' to see it."
        )
        add_message(message, logging.INFO)
        break
settings = Dynaconf(
    envar_prefix=env_var_app_name,
    env_switcher=f"{env_var_app_name}_ENV",
    # environment variable to apply mode of environment (e.g., dev, production)
    core_loaders=["YAML"],  # will not read any file extensions except YAML
    # loaders=['conf'],  # will not work without properly defining a custom loader for .conf first
    yaml_loader="safe_load",  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC],
    # the order of settings_files list is the overwrite priority order. PROJECT_CONFIG_LOC has the highest priority.
)

history = ConfigHistory(settings)
minimal_active_configuration: MinimalActiveConfiguration = MinimalActiveConfiguration()

# Host URL
HOST = settings.get(KEY_HOST, None)


# API token (api_key)
class APIToken:
    def __init__(self, token: str, /, mask_char: str = "*"):
        self.token = token
        self.mask_char = mask_char

    def __str__(self):
        return self.token and self._mask()

    def __repr__(self):
        return f"APIToken(token={self.__str__()})"

    def __eq__(self, other):
        return self.token == other

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str):
        if value is None:
            raise ValueError("token cannot be None!")
        if not isinstance(value, str):
            raise ValueError("token must be an instance of string!")
        self._token = value

    def _mask(self) -> str:
        expose_table = {
            range(4): 0,
            range(4, 7): 1,
            range(7, 15): 2,
            range(15, 20): 3,
            range(16, 35): 4,
        }
        expose = 5
        for r in expose_table:
            if len(self._token) in r:
                expose = expose_table[r]
                break
        return f"{self.token[:expose]}{self.mask_char * (expose + 1)}{self.token[:-expose-1:-1][::-1]}"


# Note elabftw-python uses the term "api_key" for "API_TOKEN"
API_TOKEN: str = settings.get(KEY_API_TOKEN, None)

# Here, bearer term "Authorization" already follows convention, that's why it's not part of the configuration file
TOKEN_BEARER: str = "Authorization"
# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

_XDG_DOWNLOAD_DIR = os.getenv(ENV_XDG_DOWNLOAD_DIR, None)

# Export location
EXPORT_DIR = settings.get(KEY_EXPORT_DIR, None)
# # Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

# App internal data location
if LOG_FILE_PATH.parent != LOG_DIR_ROOT:
    APP_DATA_DIR = LOG_FILE_PATH.parent
else:
    validate_app_dir = Validate(
        PathValidator([_XDG_DATA_HOME / APP_NAME, FALLBACK_DIR / APP_NAME])
    )
    try:
        APP_DATA_DIR = validate_app_dir.get()
    except ValidationError:
        logger.critical(
            f"{APP_NAME} couldn't validate {FALLBACK_DIR} to store {APP_NAME} internal application data. "
            f"{APP_NAME} will not run!"
        )
        raise CriticalValidationError

# The history is ready to be inspected
inspect = InspectConfigHistory(history)

# UNSAFE_TOKEN_WARNING falls back to True if not defined in configuration
UNSAFE_TOKEN_WARNING_DEFAULT_VAL: bool = True
UNSAFE_TOKEN_WARNING = settings.get(KEY_UNSAFE_TOKEN_WARNING, None)

# ENABLE_HTTP2 falls back to False if not defined in configuration
ENABLE_HTTP2_DEFAULT_VAL: bool = False
ENABLE_HTTP2 = settings.get(KEY_ENABLE_HTTP2, None)

# VERIFY_SSL falls back to True if not defined in configuration
VERIFY_SSL_DEFAULT_VAL: bool = True
VERIFY_SSL = settings.get(KEY_VERIFY_SSL, None)

# TIMEOUT falls back to 90.0 seconds if not defined in configuration
TIMEOUT_DEFAULT_VAL: float = 90.0  # from httpx._config import DEFAULT_TIMEOUT_CONFIG
TIMEOUT = settings.get(KEY_TIMEOUT, None)

# DEVELOPMENT_MODE falls back to false if not defined in configuration
DEVELOPMENT_MODE_DEFAULT_VAL: bool = False
DEVELOPMENT_MODE = settings.get(KEY_DEVELOPMENT_MODE, None)

# Plugins
PLUGIN = settings.get(KEY_PLUGIN_KEY_NAME, None)
PLUGIN_DEFAULT_VALUE: dict = {}


for key_name, key_val in [
    (KEY_HOST, HOST),
    (KEY_API_TOKEN, API_TOKEN),
    (KEY_EXPORT_DIR, EXPORT_DIR),
    (KEY_UNSAFE_TOKEN_WARNING, UNSAFE_TOKEN_WARNING),
    (KEY_ENABLE_HTTP2, ENABLE_HTTP2),
    (KEY_VERIFY_SSL, VERIFY_SSL),
    (KEY_TIMEOUT, TIMEOUT),
    (KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE),
    (KEY_PLUGIN_KEY_NAME, PLUGIN),
]:
    try:
        history.patch(key_name, key_val)
    except KeyError:
        minimal_active_configuration[key_name] = AppliedConfigIdentity(Missing(), None)
    else:
        if key_name == KEY_API_TOKEN:
            try:
                history.patch(key_name, APIToken(key_val))
            except ValueError:
                ...
        minimal_active_configuration[key_name] = InspectConfigHistory(
            history
        ).applied_config[key_name]

# Temporary data storage location
# This location is not currently used anywhere, for potential future use only.
TMP_DIR: [ProperPath, Path, Missing] = ProperPath(TMP_DIR, err_logger=logger)
try:
    TMP_DIR.create()
except TMP_DIR.PathException:
    TMP_DIR = Missing("NONE!")
else:
    TMP_DIR = TMP_DIR.expanded

# Plugin file definitions and locations
ROOT_INSTALLATION_DIR: Path = Path(__file__).parent.parent
INTERNAL_PLUGIN_DIRECTORY_NAME: str = KEY_PLUGIN_KEY_NAME.lower()
INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX: str = "cli"
INTERNAL_PLUGIN_TYPER_APP_FILE_NAME: str = (
    f"{INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX}.py"
)
INTERNAL_PLUGIN_TYPER_APP_VAR_NAME: str = "app"
# Local external/3rd-party plugin definitions
EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME: str = INTERNAL_PLUGIN_DIRECTORY_NAME
EXTERNAL_LOCAL_PLUGIN_DIR: Path = APP_DATA_DIR / EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX: str = (
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX
)
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME: str = INTERNAL_PLUGIN_TYPER_APP_FILE_NAME
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME: str = INTERNAL_PLUGIN_TYPER_APP_VAR_NAME
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX: str = f"{APP_NAME}_plugin_metadata"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT: str = CONFIG_FILE_EXTENSION
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME: str = (
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX}."
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT}"
)

EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS = (
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX}_exists"
)
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME: str = "plugin_name"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH: str = "cli_script"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH: str = "venv_dir"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH: str = "project_dir"
EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR: str = "plugin_root_dir"
