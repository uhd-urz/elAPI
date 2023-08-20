import os
from pathlib import Path
from typing import Union

# variables with leading underscores here indicate that they are to be overwritten by _config_handler.py
# In which case, import their counterparts from src/_config_handler.py
# name definitions
APP_NAME: str = "elabftw-get"
LOG_FILE_NAME: str = f"{APP_NAME}.log"
CONFIG_FILE_NAME: str = f"{APP_NAME}.yaml"
user_home: Path = Path.home()
cur_dir: Path = Path.cwd()

# reference for the following directory conventions:
# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

# XDG and other convention variable definitions
XDG_DATA_HOME: Union[str, None] = os.getenv("XDG_DATA_HOME")
XDG_DOWNLOAD_DIR: Union[str, None] = os.getenv("XDG_DOWNLOAD_DIR")
XDG_CONFIG_HOME: Union[str, None] = os.getenv('XDG_CONFIG_HOME')
TMP_DIR: Path = Path(f"/var/tmp/{APP_NAME}")

# Fallback definitions
FALLBACK_DIR: Path = user_home / ".local/share" / APP_NAME
FALLBACK_DOWNLOAD_DIR: Path = user_home / 'Downloads'
FALLBACK_CONFIG_DIR: Path = user_home / '.config'

# Configuration path definitions
SYSTEM_CONFIG_LOC: Path = Path("/etc") / CONFIG_FILE_NAME
LOCAL_CONFIG_LOC: Path = Path(XDG_CONFIG_HOME) / CONFIG_FILE_NAME if XDG_CONFIG_HOME \
    else FALLBACK_CONFIG_DIR / CONFIG_FILE_NAME
# In case, $XDG_CONFIG_HOME isn't defined in the machine, it falls back to $HOME/.config/elabftw-get.yaml
PROJECT_CONFIG_LOC: Path = cur_dir / CONFIG_FILE_NAME

# App internal data directory
APP_DATA_DIR: Path = Path(XDG_DATA_HOME) / APP_NAME if XDG_DATA_HOME else None
# APP_DATA_DIR doesn't fall back to FALLBACK_DIR here because we want to allow falling back other conventions first
# E.g., In _log_file_handler.py the priority order is, _DIRS := APP_DATA_DIR > LOG_DIR_ROOT > FALLBACK_DIR

# Log data directory with root permission
LOG_DIR_ROOT: Path = Path(f"/var/log/{APP_NAME}")

# Download data directory
_DOWNLOAD_DIR = Path(XDG_DOWNLOAD_DIR) / APP_NAME if XDG_DOWNLOAD_DIR else FALLBACK_DOWNLOAD_DIR
