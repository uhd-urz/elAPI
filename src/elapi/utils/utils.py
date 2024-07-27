import re
from typing import Any, Iterable, Tuple


class PreventiveWarning(Exception): ...


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


def missing_warning(fields: Tuple[str, Any], /) -> None:
    from .. import configuration
    from ..configuration import KEY_DEVELOPMENT_MODE
    from ..styles import Missing

    if not isinstance(fields, Iterable) and not isinstance(fields, str):
        raise TypeError(
            f"{missing_warning.__name__} only accepts an iterable of key-value pair."
        )
    try:
        key, value = fields
    except ValueError as e:
        raise ValueError(
            "Only a pair of configuration key and its value in an "
            f"iterable can be passed to {missing_warning.__name__}."
        ) from e
    if isinstance(value, Missing):
        key = key.lower()
        raise PreventiveWarning(
            f"Value for '{key}' from configuration file is missing. "
            f"This is not necessarily a critical error but a future operation might fail. "
            f"If '{key}' is supposed to fallback to a default value or if you want to "
            f"get a more precise error message, make sure to run function "
            f"'{configuration.reinitiate_config.__name__}()' (can be imported with "
            f"'from {configuration.__name__} import {configuration.reinitiate_config.__name__}') "
            f"before running anything else. You could also just define a valid value for '{key}' "
            f"in configuration file. This warning may also be shown because '{KEY_DEVELOPMENT_MODE.lower()}' "
            f"is set to '{True}' in configuration file. In most cases, just running "
            f"'{configuration.reinitiate_config.__name__}()' should fix this issue."
        )


class NoException(Exception): ...
