from datetime import datetime
from pathlib import Path

from src._path_handler import ProperPath
from src.core_names import APP_DATA_DIR, LOG_DIR_ROOT, LOG_FILE_NAME

initial_validation: dict[Path:Path] = {}
_DIRS: tuple[Path, ...] = LOG_DIR_ROOT, APP_DATA_DIR

for loc in _DIRS:
    if working_path := ProperPath(loc / LOG_FILE_NAME, suppress_stderr=True).create():
        initial_validation[loc] = working_path
        break

try:
    LOG_FILE_PATH, *_ = initial_validation.values()
except ValueError as e:
    raise PermissionError(
        f"{datetime.now().isoformat(sep=' ', timespec='seconds')}:FATAL: Permission to write logs in fallback path "
        f"{APP_DATA_DIR}/{LOG_FILE_NAME} is denied as well! This is a critical error.\n"
        f"elabftw-get will not run!") from e

LOG_FILE_PATH: Path = LOG_FILE_PATH.expanded
