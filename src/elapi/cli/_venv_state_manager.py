from pathlib import Path
from typing import Union

from ..path import ProperPath

VENV_INDICATOR_DIR_NAME: str = "site-packages"


def switch_venv_state(
    state: bool,
    /,
    venv_dir: Union[Path, ProperPath],
    project_dir: Union[Path, ProperPath],
):
    import sys

    project_dir = str(project_dir)
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
        if state is True:
            sys.path.insert(1, unique_dir)
            sys.path.insert(1, project_dir)
            return
        else:
            if sys.path[1:3] == [project_dir, unique_dir]:
                sys.path.pop(1)
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
                    try:
                        sys.path.remove(project_dir)
                    except ValueError as e:
                        raise RuntimeError(
                            f"Project directory {project_dir} "
                            f"couldn't be removed from sys.path!"
                        ) from e
                    return
