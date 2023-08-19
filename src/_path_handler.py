import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from src.loggers import logger


@dataclass()
class ProperPath:
    name: Union[str, Path]
    env_var: bool = False

    def __post_init__(self) -> None:
        if self.name == "":
            raise ValueError("Path cannot be an empty string!")

    def expand(self) -> Union[Path, None]:
        if self.env_var:
            env_var_val: Union[str, None] = os.getenv(self.name)
            return Path(env_var_val).expanduser() if env_var_val else None
        return Path(self.name).expanduser()

    def resolve(self, strict: bool = True) -> Union[Path, None]:
        # resolve() returns None if a path couldn't be resolved.
        path = self.expand()

        if path:
            try:
                path = path.resolve(strict=strict)
            except FileNotFoundError:
                logger.warning(
                    f"<'{self.name}':'{path}'> could not be found. elabftw-get will attempt to create the '{path}'.")

            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                logger.critical(f"Permission has been denied to create <'{self.name}':'{path}'>")

            else:
                return path
