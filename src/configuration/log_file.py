import os

from src._names import (
    FALLBACK_DIR,
    LOG_DIR_ROOT,
    LOG_FILE_NAME,
    APP_NAME,
    ENV_XDG_DATA_HOME,
)
from src.loggers import Logger
from src.path import ProperPath
from src.validators import Validate, ValidationError, PathValidator

logger = Logger(suppress_stderr=True)

validate_path = Validate(
    PathValidator(
        [
            LOG_DIR_ROOT,
            (XDG_DATA_HOME := ProperPath(os.getenv(ENV_XDG_DATA_HOME, os.devnull)))
            / APP_NAME,
            FALLBACK_DIR,
        ],
        err_logger=logger,
    )
)

try:
    LOG_FILE_PATH = validate_path.get() / LOG_FILE_NAME
except ValidationError as e:
    logger.critical(
        f"{APP_NAME} couldn't validate fallback path {FALLBACK_DIR}/{LOG_FILE_NAME} to write logs! "
        f"This is a critical error. {APP_NAME} will not run!"
    )
    raise SystemExit() from e
