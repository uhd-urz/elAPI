import re
from pathlib import Path

from .._names import VERSION_FILE_NAME
from ..styles import Missing


class PreventiveWarning(RuntimeWarning): ...


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


class NoException(Exception): ...
