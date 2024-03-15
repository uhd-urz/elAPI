import re
from typing import Tuple


def get_location_from_headers(header: dict, key: str = "location") -> Tuple[str, str]:
    try:
        location_backwards = (location := header[key].rstrip("/"))[::-1]
    except KeyError as e:
        raise ValueError(f"Argument 'header' doesn't contain the key '{key}'") from e
    _start, _end = re.match("\d+(?=/)", location_backwards).span()
    return location_backwards[_start:_end][::-1], location
