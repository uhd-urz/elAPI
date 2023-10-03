from pathlib import Path

from src._names import (
    FALLBACK_DIR,
    LOG_DIR_ROOT,
    LOG_FILE_NAME,
    APP_NAME,
    XDG_DATA_HOME,
)
from src.validators import Validate, ValidationError, PathValidator
from src.loggers import Logger

logger = Logger(suppress_stderr=True)

_DIRS: tuple[Path, ...] = LOG_DIR_ROOT, XDG_DATA_HOME / APP_NAME, FALLBACK_DIR

validate_path = Validate(PathValidator(_DIRS, err_logger=logger))

try:
    LOG_FILE_PATH = validate_path() / LOG_FILE_NAME
except ValidationError as e:
    logger.critical(
        f"{APP_NAME} couldn't validate fallback path {FALLBACK_DIR}/{LOG_FILE_NAME} to write logs! "
        f"This is a critical error. {APP_NAME} will not run!"
    )
    raise SystemExit() from e
