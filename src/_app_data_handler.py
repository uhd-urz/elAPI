from pathlib import Path
import os

USER_HOME = Path(os.getenv('HOME'))
APP_DATA_PARENT_DIR_NAME = "elabftw-get"

# Reference: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# App internal data location
XDG_DATA_HOME = os.getenv('XDG_DATA_HOME')
ASSUMED_LOCAL_DATA_DIR = USER_HOME / '.local/share'  # if XDG_DATA_HOME isn't defined in the machine
APP_DATA_DIR = Path(XDG_DATA_HOME) / APP_DATA_PARENT_DIR_NAME if XDG_DATA_HOME \
    else Path(ASSUMED_LOCAL_DATA_DIR) / APP_DATA_PARENT_DIR_NAME
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)  # parents=True => mkdir -p

# App log data location
LOG_DIR = APP_DATA_DIR

# API response data location
RESPONSE_DATA_DIR = Path('/var/tmp/elabftw-get')
RESPONSE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Download location
XDG_DOWNLOAD_DIR = os.getenv('XDG_DOWNLOAD_DIR')
DOWNLOAD_DIR = Path(XDG_DOWNLOAD_DIR) if XDG_DOWNLOAD_DIR \
    else Path(USER_HOME) / 'Downloads'  # Assumes ~/Downloads if $XDG_DOWNLOAD_DIR isn't found
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
