import sys
from datetime import datetime
from pathlib import Path
from typing import Union

from src.core_names import FALLBACK_DIR, APP_DATA_DIR, LOG_DIR_ROOT, LOG_FILE_NAME

# loggers.py gets its path for storing log from _log_file_handler.py
# Therefore _log_file_handler.py cannot depend on ProperPath in _path_handler.py


LOG_DIR: Union[Path, str] = ""
_DIRS: tuple[Path, ...] = APP_DATA_DIR, LOG_DIR_ROOT, FALLBACK_DIR

for _, loc in enumerate(_DIRS):
    if loc:
        try:
            loc.mkdir(parents=True, exist_ok=True)
            (loc / LOG_FILE_NAME).touch(exist_ok=True)
        except PermissionError:
            print(f"{datetime.now().isoformat(sep=' ', timespec='seconds')}:WARNING: Permission to write logs in "
                  f"'{loc}/{LOG_FILE_NAME}' has been denied.", file=sys.stderr)
            print(f"Falling back to write logs in '{_DIRS[_ + 1]}/{LOG_FILE_NAME}'.", file=sys.stderr) \
                if _ + 1 < len(_DIRS) else ...
        else:
            LOG_DIR = loc
            break

if not LOG_DIR:
    raise PermissionError(
        f"{datetime.now().isoformat(sep=' ', timespec='seconds')}: FATAL: Permission to write logs in fallback path "
        f"{FALLBACK_DIR}/{LOG_FILE_NAME} has been denied as well! This is a critical error.\n"
        f"elabftw-get will not run!")

LOG_FILE_PATH: Path = LOG_DIR / LOG_FILE_NAME
