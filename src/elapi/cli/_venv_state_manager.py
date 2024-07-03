from pathlib import Path
from typing import Union

from ..path import ProperPath

VENV_INDICATOR_DIR_NAME: str = "site-packages"


def switch_venv_state(status: bool, /, venv_dir: Union[Path, ProperPath]):
    import sys

    site_packages = sorted(
        venv_dir.rglob(VENV_INDICATOR_DIR_NAME), key=lambda x: str(x).lower()
    )

    if not site_packages:
        raise ValueError(
            f"Could not find '{VENV_INDICATOR_DIR_NAME}' directory in "
            "virtual environment path."
        )
    for unique_dir in site_packages:
        unique_dir = str(unique_dir)
        if status is True:
            sys.path.insert(1, unique_dir)
            return
        else:
            if sys.path[1] == unique_dir:
                sys.path.pop(1)
                return
            else:
                try:
                    sys.path.remove(unique_dir)
                except ValueError as e:
                    raise RuntimeError(
                        f"Virtual environment directory "
                        f"{unique_dir} couldn't be removed from sys.path!"
                    ) from e
                else:
                    return
