import os
from contextlib import redirect_stderr, redirect_stdout

from .._names import (
    FALLBACK_DIR,
    LOG_DIR_ROOT,
    LOG_FILE_NAME,
    APP_NAME,
    ENV_XDG_DATA_HOME,
)
from .._core_init import Logger
from ..path import ProperPath
from ..core_validators import (
    Validate,
    ValidationError,
    CriticalValidationError,
    PathValidator,
)

logger = Logger()

validate_path = Validate(
    PathValidator(
        [
            LOG_DIR_ROOT / LOG_FILE_NAME,
            (_XDG_DATA_HOME := ProperPath(os.getenv(ENV_XDG_DATA_HOME, os.devnull)))
            / APP_NAME
            / LOG_FILE_NAME,
            FALLBACK_DIR / LOG_FILE_NAME,
        ]
    )
)

try:
    with open(os.devnull, "w") as devnull:
        with redirect_stderr(devnull), redirect_stdout(devnull):
            LOG_FILE_PATH = validate_path.get()
except ValidationError as e:
    logger.critical(
        f"{APP_NAME} couldn't validate fallback path {FALLBACK_DIR}/{LOG_FILE_NAME} to write logs! "
        f"This is a critical error. {APP_NAME} will not run!"
    )
    raise CriticalValidationError from e
