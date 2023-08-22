import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Union


class ProperPath:
    def __init__(self, name: Union[str, Path, None],
                 env_var: bool = False,
                 kind: Union[str, None] = '',
                 suppress_stderr: bool = False):

        self.name = name
        self.env_var = env_var
        self.kind = kind
        self.suppress_stderr = suppress_stderr

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == "":
            raise ValueError("Path cannot be an empty string!")
        self._name = value

    @property
    def expanded(self):
        if self.env_var:
            env_var_val: Union[str, None] = os.getenv(self.name)
            return Path(env_var_val).expanduser() if env_var_val else None
        else:
            return Path(self.name).expanduser() if self.name else None

    @expanded.setter
    def expanded(self, value):
        raise AttributeError("Expanded is not meant to be modified.")

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, value):
        if self.expanded:
            if not value:
                self._kind = 'file' if self.expanded.suffix else 'dir'
            else:
                # TODO: Python pattern matching doesn't support regex matching yet.
                if re.match(r'\bfile\b', value, flags=re.IGNORECASE):
                    self._kind = 'file'
                elif re.match(r'\bdir(ectory)?\b|\b(folder)\b', value, flags=re.IGNORECASE):
                    self._kind = 'dir'
                else:
                    raise ValueError(
                        "Invalid value for parameter 'kind'. The following values for 'kind' are allowed: file, dir.")

    def path_error_logger(self, message: str, level: int = logging.DEBUG):
        LOG_LEVELS = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}

        try:
            from src.loggers import logger, stdout_handler
        except ImportError:
            if not self.suppress_stderr:
                print(f"{datetime.now().isoformat(sep=' ', timespec='seconds')}:{LOG_LEVELS[level]}: {message}",
                      file=sys.stderr)
        else:
            if self.suppress_stderr:
                logger.removeHandler(stdout_handler)
            logger.log(msg=message, level=level)

    def resolve(self) -> Union[Path, None]:
        # resolve() returns None if a path cannot be resolved.
        path = self.expanded

        if path:
            if not (path := path.resolve(strict=False)).exists():
                # except FileNotFoundError:
                message = f"<'{self.name}':'{path}'> could not be found. An attempt to create '{path}' will be made."
                self.path_error_logger(message, level=logging.WARNING)

            try:
                if self.kind == 'file':
                    path_parent, path_file = path.parent, path.name
                    path_parent.mkdir(parents=True, exist_ok=True)
                    (path_parent / path_file).touch(exist_ok=True)
                elif self.kind == 'dir':
                    path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                message = f"Permission is denied to create <'{self.name}':'{path}'>"
                self.path_error_logger(message, level=logging.CRITICAL)
            else:
                return path
