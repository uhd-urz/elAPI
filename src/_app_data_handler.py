from pathlib import Path
import os

APP_DATA_PARENT_DIR_NAME = "elabftw-get"

# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# App unit_data
LOCAL_DATA_DIR = os.getenv('XDG_DATA_HOME')
ASSUMED_LOCAL_DATA_DIR = os.getenv('HOME') + '/.local/share'  # based on popular convention
APP_DATA_DIR = Path(LOCAL_DATA_DIR) / APP_DATA_PARENT_DIR_NAME if LOCAL_DATA_DIR else Path(
    ASSUMED_LOCAL_DATA_DIR) / APP_DATA_PARENT_DIR_NAME
APP_DATA_DIR.mkdir(exist_ok=True)

# App log unit_data
LOG_DIR = APP_DATA_DIR

# API response unit_data
RESPONSE_DATA_DIR = Path('/var/tmp/elabftw-get')
RESPONSE_DATA_DIR.mkdir(exist_ok=True)
