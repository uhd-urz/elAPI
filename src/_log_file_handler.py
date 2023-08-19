import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Union

# loggers.py gets its path for storing log from _log_file_handler.py
# Therefore _log_file_handler.py cannot depend on ProperPath in _path_handler.py

# the following constants (_APP_NAME, _USER_HOME, _FALLBACK_DIR) are allowed to be imported but
# to avoid circular dependency issue, they must be assigned to additional variable names right after being imported.
_APP_NAME: str = "elabftw-get"
_USER_HOME: Path = Path.home()
_FALLBACK_DIR: Path = _USER_HOME / ".local/share" / _APP_NAME

XDG_DATA_HOME: Union[str, None] = os.getenv("XDG_DATA_HOME")
_LOG_DIR_USER: Path = Path(XDG_DATA_HOME) / _APP_NAME if XDG_DATA_HOME else None
LOG_DIR_ROOT: Path = Path("/var/log/elabftw-get")
LOG_DIR: Union[Path, str] = ""

LOG_FILE_NAME: str = f"{_APP_NAME}.log"

_DIRS: tuple[Path, ...] = _LOG_DIR_USER, LOG_DIR_ROOT, _FALLBACK_DIR

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
        f"{datetime.now().isoformat(sep=' ', timespec='seconds')}: WARNING: Permission to write logs in fallback path "
        f"{_FALLBACK_DIR} has been denied as well! This is a critical error.\n"
        f"elabftw-get will not run!")

LOG_FILE_PATH: Path = LOG_DIR / LOG_FILE_NAME
