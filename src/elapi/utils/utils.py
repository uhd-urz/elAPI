import re
import subprocess
from pathlib import Path
from typing import Tuple

from .._names import VERSION_FILE_NAME
from ..styles import Missing


class PreventiveWarning(RuntimeWarning): ...


class PythonVersionCheckFailed(Exception): ...


def check_reserved_keyword(
    error_instance: Exception, /, *, what: str, against: str
) -> None:
    if re.search(
        r"got multiple values for keyword argument",
        error_verbose := str(error_instance),
        re.IGNORECASE,
    ):
        _reserved_key_end = re.match(
            r"^'\w+'", error_verbose[::-1], re.IGNORECASE
        ).end()
        raise AttributeError(
            f"{what} reserves the keyword argument "
            f"'{error_verbose[- _reserved_key_end + 1: - 1]}' "
            f"for {against}."
        ) from error_instance


def get_sub_package_name(dunder_package: str, /) -> str:
    if not isinstance(dunder_package, str):
        raise TypeError(
            f"{get_sub_package_name.__name__} only accepts __package__ as string."
        )
    match = re.match(r"(^[a-z_]([a-z0-9_]+)?)\.", dunder_package[::-1], re.IGNORECASE)
    # Pattern almost follows: https://packaging.python.org/en/latest/specifications/name-normalization/
    if match is not None:
        return match.group(1)[::-1]
    raise ValueError("No matching sub-package name found.")


def update_kwargs_with_defaults(kwargs: dict, /, defaults: dict) -> None:
    key_arg_missing = Missing("Keyword argument missing")
    for default_key, default_val in defaults.items():
        if kwargs.get(default_key, key_arg_missing) is key_arg_missing:
            kwargs.update({default_key: default_val})


def get_app_version() -> str:
    return Path(f"{__file__}/../../{VERSION_FILE_NAME}").resolve().read_text().strip()


def _get_venv_relative_python_binary_path() -> Path:
    return Path("bin/python")


def get_external_python_version(venv_dir: Path) -> Tuple[str, str, str]:
    external_python_path: Path = (
        venv_dir / _get_venv_relative_python_binary_path()
    ).resolve()
    if external_python_path.exists() is False:
        raise PythonVersionCheckFailed(
            f"Resolved Python binary path {external_python_path} does not exist"
        )
    try:
        external_python_version_call = subprocess.run(
            [str(external_python_path), "--version"],
            check=True,
            encoding="utf-8",
            timeout=5,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise PythonVersionCheckFailed(e) from e
    except TimeoutError as e:
        raise PythonVersionCheckFailed(e) from e
    else:
        external_python_version_match = re.search(
            r"^Python (\d+)\.(\d+)\.(\d+)$",  # ensures 3 strings in match.groups()
            external_python_version_call.stdout,
            flags=re.IGNORECASE,
        )
        if external_python_version_match is not None:
            # noinspection PyTypeChecker
            external_python_version: Tuple[str, str, str] = (
                external_python_version_match.groups()
            )
            return external_python_version
        raise PythonVersionCheckFailed(
            "Matching Python version not found in output string"
        )


class NoException(Exception): ...
