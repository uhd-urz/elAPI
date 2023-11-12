import os
from pathlib import Path
from typing import Union

from .path import ProperPath

# variables with leading underscores here indicate that they are to be overwritten by config.py
# In which case, import their counterparts from src/config.py
# name definitions
APP_NAME: str = "elapi"
LOG_FILE_NAME: str = f"{APP_NAME}.log"
CONFIG_FILE_NAME: str = f"{APP_NAME}.yaml"
user_home: Path = Path.home()
cur_dir: Path = Path.cwd()

# reference for the following directory conventions:
# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

# XDG and other convention variable definitions
ENV_XDG_DATA_HOME: Union[ProperPath, Path, str] = "XDG_DATA_HOME"
ENV_XDG_DOWNLOAD_DIR: Union[ProperPath, Path, str] = "XDG_DOWNLOAD_DIR"
ENV_XDG_CONFIG_HOME: Union[ProperPath, Path, str] = "XDG_CONFIG_HOME"
TMP_DIR: Path = Path(f"/var/tmp/{APP_NAME}")

# Fallback definitions
FALLBACK_DIR: Path = user_home / ".local/share" / APP_NAME
FALLBACK_EXPORT_DIR: Path = user_home / "Downloads"
FALLBACK_CONFIG_DIR: Path = user_home / ".config"

# Configuration path definitions
SYSTEM_CONFIG_LOC: Path = Path("/etc") / CONFIG_FILE_NAME
LOCAL_CONFIG_LOC: Path = (
    os.getenv(ENV_XDG_CONFIG_HOME) or FALLBACK_CONFIG_DIR
) / CONFIG_FILE_NAME
# In case, $XDG_CONFIG_HOME isn't defined in the machine, it falls back to $HOME/.config/elapi.yaml
PROJECT_CONFIG_LOC: Path = cur_dir / CONFIG_FILE_NAME

# Configuration field definitions
KEY_HOST: str = "HOST"
KEY_API_TOKEN: str = "API_TOKEN"
KEY_EXPORT_DIR: str = "EXPORT_DIR"
KEY_UNSAFE_TOKEN_WARNING: str = "UNSAFE_API_TOKEN_WARNING"

# Log data directory with root permission
LOG_DIR_ROOT: Path = Path(f"/var/log/{APP_NAME}")
