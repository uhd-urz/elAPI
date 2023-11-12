import os
from pathlib import Path

from dynaconf import Dynaconf

from .._names import (
    APP_NAME,
    ENV_XDG_DOWNLOAD_DIR,
    FALLBACK_DIR,
    FALLBACK_EXPORT_DIR,
    CONFIG_FILE_NAME,
    TMP_DIR,
    SYSTEM_CONFIG_LOC,
    PROJECT_CONFIG_LOC,
    LOCAL_CONFIG_LOC,
    LOG_DIR_ROOT,
    KEY_HOST,
    KEY_API_TOKEN,
    KEY_EXPORT_DIR,
    KEY_UNSAFE_TOKEN_WARNING,
)
from ._config_history import ConfigHistory, InspectConfigHistory
from .log_file import LOG_FILE_PATH, XDG_DATA_HOME
from ..loggers import Logger
from ..path import ProperPath
from ..validators import (
    Validate,
    ValidationError,
    CriticalValidationError,
    PathValidator,
)

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
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC],
    # the order of settings_files list is the overwrite priority order. PROJECT_CONFIG_LOC has the highest priority.
)

history = ConfigHistory(settings)

# Host URL
HOST: str = settings.get(
    KEY_HOST
)  # case-insensitive: settings.get("HOST") == settings.get("host")
if not HOST:
    logger.critical(
        f"'host' is empty or missing from {CONFIG_FILE_NAME} file. "
        f"Please make sure host (URL pointing to root API endpoint) is included."
    )


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


API_TOKEN: str = settings.get(KEY_API_TOKEN)
if not API_TOKEN:
    logger.critical(
        f"'api_token' is empty or missing from {CONFIG_FILE_NAME} file. "
        f"Please make sure api token with at least read access is included."
    )
    # Note elabftw-python uses the term "api_key" for "API_TOKEN"
else:
    history.patch(KEY_API_TOKEN, APIToken(API_TOKEN))

# Here, bearer term "Authorization" already follows convention, that's why it's not part of the configuration file
TOKEN_BEARER: str = "Authorization"
# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

# Export location
CONFIG_EXPORT_DIR = ProperPath(
    (_CONFIG_EXPORT_DIR_ORIGINAL := settings.get(KEY_EXPORT_DIR)) or os.devnull,
    err_logger=logger,
)  # the default "os.devnull" saves ProperPath from TypeError, ValueError
# for when settings.get(KEY_EXPORT_DIR) is None/"".
if _CONFIG_EXPORT_DIR_ORIGINAL and CONFIG_EXPORT_DIR.kind != "dir":
    logger.warning(
        f"{KEY_EXPORT_DIR}: {_CONFIG_EXPORT_DIR_ORIGINAL} is not a directory!"
    )
    logger.debug("If you want to export to a file use '--export <path-to-file>'.")
    CONFIG_EXPORT_DIR = None
try:
    EXPORT_DIR = Validate(PathValidator(CONFIG_EXPORT_DIR)).get()
except ValidationError:
    if _CONFIG_EXPORT_DIR_ORIGINAL:
        logger.warning(
            f"{KEY_EXPORT_DIR}: {_CONFIG_EXPORT_DIR_ORIGINAL} from configuration file couldn't be validated! "
        )
    try:
        history.delete(KEY_EXPORT_DIR)
    except KeyError:
        ...
    try:
        EXPORT_DIR = Validate(
            PathValidator(
                [
                    os.getenv(ENV_XDG_DOWNLOAD_DIR, None),
                    FALLBACK_EXPORT_DIR,
                ]
            )
        ).get()
    except ValidationError:
        logger.critical(
            f"{APP_NAME} couldn't validate {FALLBACK_EXPORT_DIR} to store exported data. "
            f"This is a fatal error. To quickly fix this error define an export directory "
            f"with 'export_dir' in configuration file. {APP_NAME} will not run!"
        )
        raise CriticalValidationError
# Falls back to ~/Downloads if $XDG_DOWNLOAD_DIR isn't found

# App internal data location
if LOG_FILE_PATH.parent != LOG_DIR_ROOT:
    APP_DATA_DIR = LOG_FILE_PATH.parent
else:
    validate_app_dir = Validate(
        PathValidator([XDG_DATA_HOME / APP_NAME, FALLBACK_DIR / APP_NAME])
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
try:
    settings[KEY_UNSAFE_TOKEN_WARNING]
except KeyError:
    UNSAFE_TOKEN_WARNING: bool = True
else:
    UNSAFE_TOKEN_WARNING: bool = settings.as_bool(KEY_UNSAFE_TOKEN_WARNING)
    # equivalent to settings.get(<key>, cast='@bool')
try:
    if UNSAFE_TOKEN_WARNING and inspect.applied_config[KEY_API_TOKEN].source == str(
        PROJECT_CONFIG_LOC
    ):
        logger.warning(
            f"'{KEY_API_TOKEN}' field in project-based configuration file {PROJECT_CONFIG_LOC} found. "
            f"This is highly discouraged. The token is at risk of being leaked into public repositories. "
            f"If you still insist, please make sure {CONFIG_FILE_NAME} is included in .gitignore."
        )
except KeyError:
    ...
# Temporary data storage location
# elapi will dump API response data in TMP_DIR so the data can be used for debugging purposes.
TMP_DIR: Path = ProperPath(TMP_DIR, err_logger=logger).create()
