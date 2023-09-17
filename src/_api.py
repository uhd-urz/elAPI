from abc import ABC, abstractmethod
from typing import Union

from httpx import Response, Client, AsyncClient
from httpx_auth import HeaderApiKey

from src._config_handler import API_TOKEN, TOKEN_BEARER, HOST


class APIRequest(ABC):
    __slots__ = "host", "api_token", "header_name", "keep_session_open", "_client"

    def __init__(self, keep_session_open: bool = False, **kwargs):
        self.host: str = HOST
        self.api_token: str = API_TOKEN
        self.header_name: str = TOKEN_BEARER
        self.keep_session_open = keep_session_open
        _client = Client if not self.is_async_client else AsyncClient
        self._client: Union[Client, AsyncClient] = _client(
            auth=HeaderApiKey(api_key=self.api_token, header_name=self.header_name),
            verify=True, **kwargs)

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, /, is_async_client: bool, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.is_async_client = is_async_client

    @property
    def client(self) -> Union[Client, AsyncClient]:
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


class GETRequest(APIRequest, is_async_client=False):
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


class POSTRequest(APIRequest, is_async_client=False):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(async_client=False, **kwargs)

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


class AsyncGETRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _make(self, *args) -> Response:
        endpoint, unit_id = args
        return await super().client.get(f'{self.host}/{endpoint}/{unit_id}', headers={"Accept": "application/json"})

    async def close(self):
        await self.client.aclose()

    async def __call__(self, endpoint: str, unit_id: Union[str, int, None] = None) -> Response:
        response = await self._make(endpoint, unit_id)
        if not self.keep_session_open:
            await self.close()
        return response
