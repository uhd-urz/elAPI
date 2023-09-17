from abc import ABC, abstractmethod
from typing import Union

from httpx import Response, Client
from httpx_auth import HeaderApiKey

from src._config_handler import API_TOKEN, TOKEN_BEARER, HOST


class APIRequest(ABC):
    __slots__ = "host", "api_token", "header_name", "keep_session_open", "_client"

    def __init__(self, keep_session_open: bool = False):
        self.host: str = HOST
        self.api_token: str = API_TOKEN
        self.header_name: str = TOKEN_BEARER
        self.keep_session_open = keep_session_open
        self._client: Client = Client(
            auth=HeaderApiKey(api_key=self.api_token, header_name=self.header_name),
            verify=True)

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, value):
        raise AttributeError("Client cannot be modified!")

    @abstractmethod
    def _make(self, *args, **kwargs):
        ...

    @abstractmethod
    def close(self):
        self.client.close()

    @abstractmethod
    def __call__(self, *args, **kwargs):
        response = self._make(*args, **kwargs)
        if not self.keep_session_open:
            self.close()
        return response


# @dataclass
class GETRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args) -> Response:
        endpoint, unit_id = args
        return super().client.get(f'{self.host}/{endpoint}/{unit_id}', headers={"Accept": "application/json"})

    def close(self):
        super().close()

    def __call__(self, endpoint: str, unit_id: Union[str, int, None] = None) -> Response:
        return super().__call__(endpoint, unit_id)


class POSTRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id = args
        data = {k: v.strip() if isinstance(v, str) else v for k, v in kwargs.items()}
        return super().client.post(f'{HOST}/{endpoint}/{unit_id}',
                                   headers={"Accept": "*/*", "Content-Type": "application/json"}, json=data)

    def close(self):
        super().close()

    def __call__(self, endpoint: str, unit_id: Union[str, int, None] = None,
                 **data: Union[str, int, None]) -> Response:
        return super().__call__(endpoint, unit_id, **data)
