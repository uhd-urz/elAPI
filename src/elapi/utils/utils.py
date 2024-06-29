import re


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


class NoException(Exception): ...
