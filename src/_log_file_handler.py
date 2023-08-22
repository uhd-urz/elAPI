from datetime import datetime
from pathlib import Path
from typing import Union

from src._path_handler import ProperPath
from src.core_names import APP_DATA_DIR, LOG_DIR_ROOT, LOG_FILE_NAME

initial_validation: dict[Path:Union[Path, None]] = {}
_DIRS: tuple[Path, ...] = LOG_DIR_ROOT, APP_DATA_DIR

for loc in _DIRS:
    initial_validation[loc] = ProperPath(loc, suppress_stderr=True).resolve()

LOG_DIR, *_ = [loc for loc in initial_validation.values() if loc is not None]

if not LOG_DIR:
    raise PermissionError(
        f"{datetime.now().isoformat(sep=' ', timespec='seconds')}:FATAL: Permission to write logs in fallback path "
        f"{APP_DATA_DIR}/{LOG_FILE_NAME} is denied as well! This is a critical error.\n"
        f"elabftw-get will not run!")

LOG_FILE_PATH: Path = LOG_DIR / LOG_FILE_NAME
