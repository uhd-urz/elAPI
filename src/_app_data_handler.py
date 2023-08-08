from pathlib import Path
import os

APP_DATA_PARENT_DIR_NAME = "elabftw-get"

# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# App internal data location
LOCAL_DATA_DIR = os.getenv('XDG_DATA_HOME')
ASSUMED_LOCAL_DATA_DIR = os.getenv('HOME') + '/.local/share'  # if XDG_DATA_HOME isn't defined in the machine
APP_DATA_DIR = Path(LOCAL_DATA_DIR) / APP_DATA_PARENT_DIR_NAME if LOCAL_DATA_DIR else Path(
    ASSUMED_LOCAL_DATA_DIR) / APP_DATA_PARENT_DIR_NAME
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)  # parents=True => mkdir -p

# App log data location
LOG_DIR = APP_DATA_DIR

# API response data location
RESPONSE_DATA_DIR = Path('/var/tmp/elabftw-get')
RESPONSE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Download location
XDG_DOWNLOAD_DIR = os.getenv('XDG_DOWNLOAD_DIR')
DOWNLOAD_DIR = Path(XDG_DOWNLOAD_DIR) if XDG_DOWNLOAD_DIR \
    else Path(os.getenv('HOME')) / 'Downloads'
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
