from typing import Union

import httpx
from httpx import Response
from httpx_auth import HeaderApiKey

from src._config_handler import API_TOKEN, TOKEN_BEARER, HOST


def elabftw_fetch(endpoint: str, unit_id: int = None) -> Response:
    with httpx.Client(auth=HeaderApiKey(api_key=API_TOKEN, header_name=TOKEN_BEARER), verify=True) as client:
        response = client.get(f'{HOST}/{endpoint}/{unit_id}', headers={"Accept": "application/json"})
    return response


def elabftw_throw(endpoint: str, *, unit_id: int = None, **data: Union[str, dict, int, None]) -> Response:
    data = {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}
    # Email address starting with a space makes email address invalid! Hence, v.strip()
    with httpx.Client(auth=HeaderApiKey(api_key=API_TOKEN, header_name=TOKEN_BEARER), verify=True) as client:
        response = client.post(f'{HOST}/{endpoint}/{unit_id}',
                               headers={"Accept": "*/*", "Content-Type": "application/json"}, json=data)
    return response
