from pathlib import Path

from src._names import APP_DATA_DIR, LOG_DIR_ROOT, LOG_FILE_NAME, APP_NAME
from src.loggers import Logger
from src.path import ProperPath

logger = Logger()

initial_validation: dict[Path:Path] = {}
_DIRS: tuple[Path, ...] = LOG_DIR_ROOT, APP_DATA_DIR

for loc in _DIRS:
    if working_path := ProperPath(loc / LOG_FILE_NAME, err_logger=Logger(suppress_stderr=True)).create():
        initial_validation[loc] = working_path
        break

try:
    LOG_FILE_PATH, *_ = initial_validation.values()
except ValueError as e:
    logger.critical(f'Permission to write logs in fallback path {APP_DATA_DIR}/{LOG_FILE_NAME} is denied as well! '
                    f'This is a critical error. {APP_NAME} will not run!"')
    raise SystemExit() from e

LOG_FILE_PATH: Path = LOG_FILE_PATH  # same variable but type annotated
