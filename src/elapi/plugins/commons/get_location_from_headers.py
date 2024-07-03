import re
from typing import Tuple, Union

import httpx


def get_location_from_headers(
    header: Union[dict, httpx.Headers], key: str = "location"
) -> Tuple[str, str]:
    if isinstance(header, httpx.Headers):
        header = dict(header)
    if not isinstance(header, dict):
        raise ValueError(
            f"Argument 'header' must be a dictionary or an instance of '{httpx.Headers}'!"
        )
    try:
        location_backwards = (location := header[key].rstrip("/"))[::-1]
    except KeyError as e:
        raise ValueError(f"Argument 'header' doesn't contain the key '{key}'") from e
    try:
        _start, _end = re.match(
            pattern := r"^[\w-]+(?=/)|^[\w-]+(?==)", location_backwards
        ).span()
    except AttributeError:
        # noinspection PyUnboundLocalVariable
        raise ValueError(
            f"'location' didn't match the pattern '{pattern}' in 'header'."
        )
    return location_backwards[_start:_end][::-1], location
