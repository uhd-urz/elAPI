from abc import ABC, abstractmethod
from typing import Union

from httpx import Response, Client, AsyncClient, Limits
from httpx_auth import HeaderApiKey

from .configuration import API_TOKEN, TOKEN_BEARER, HOST


class APIRequest(ABC):
    __slots__ = "keep_session_open", "_client"
    host: str = HOST
    api_token: str = API_TOKEN
    header_name: str = TOKEN_BEARER

    def __init__(self, keep_session_open: bool = False, **kwargs):
        self.keep_session_open = keep_session_open
        _client = Client if not self.is_async_client else AsyncClient
        self._client: Union[Client, AsyncClient] = _client(
            auth=HeaderApiKey(api_key=self.api_token, header_name=self.header_name),
            verify=True,
            **kwargs,
        )

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, /, is_async_client: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.is_async_client = is_async_client

    @property
    def client(self) -> Union[Client, AsyncClient]:
        return self._client

    @client.setter
    def client(self, value):
        raise AttributeError("Client cannot be modified!")

    @staticmethod
    def fix_none(value: None):
        # When endpoint == 'users', id == 'None', requesting endpoint/id == endpoint/'None' yields all users!
        return "" if value is None else value

    @abstractmethod
    def _make(self, *args, **kwargs):
        ...

    @abstractmethod
    def close(self):
        if not self.client.is_closed:
            self.client.close()

    @abstractmethod
    def __call__(self, *args, **kwargs):
        response = self._make(*args, **kwargs)
        if not self.keep_session_open:
            self.close()
        return response


class GETRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args) -> Response:
        endpoint, unit_id = args
        unit_id = self.fix_none(unit_id)
        return super().client.get(
            f"{self.host}/{endpoint}/{unit_id}", headers={"Accept": "application/json"}
        )

    def close(self):
        super().close()

    def __call__(
        self, endpoint: str, unit_id: Union[str, int, None] = None
    ) -> Response:
        return super().__call__(endpoint, unit_id)


class POSTRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id = args
        unit_id = self.fix_none(unit_id)
        data = {k: v.strip() if isinstance(v, str) else v for k, v in kwargs.items()}
        return super().client.post(
            f"{HOST}/{endpoint}/{unit_id}",
            headers={"Accept": "*/*", "Content-Type": "application/json"},
            json=data,
        )

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        **data: Union[str, int, None],
    ) -> Response:
        return super().__call__(endpoint, unit_id, **data)


class AsyncGETRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(
            timeout=60,
            limits=Limits(
                max_connections=100, max_keepalive_connections=50, keepalive_expiry=60
            ),
            **kwargs,
        )

    async def _make(self, *args) -> Response:
        endpoint, unit_id = args
        unit_id = self.fix_none(unit_id)
        return await super().client.get(
            f"{self.host}/{endpoint}/{unit_id}", headers={"Accept": "application/json"}
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self, endpoint: str, unit_id: Union[str, int, None] = None
    ) -> Response:
        response = await self._make(endpoint, unit_id)
        if not self.keep_session_open:
            await self.close()
        return response
