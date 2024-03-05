import re
from abc import ABC, abstractmethod
from typing import Union, Optional, Tuple

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

    @abstractmethod
    def _make(self, *args, **kwargs): ...

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


class ElabFTWURL:
    VALID_ENDPOINTS: dict[str : Tuple[str]] = {
        "apikeys": (),
        "config": (),
        "experiments": (
            "uploads",
            "revisions",
            "comments",
            "items_links",
            "experiments_links",
            "steps",
            "tags",
        ),
        "info": (),
        "items": (
            "uploads",
            "revisions",
            "comments",
            "items_links",
            "experiments_links",
            "steps",
            "tags",
        ),
        "experiments_templates": (
            "revisions",
            "steps",
            "tags",
        ),
        "items_types": (
            "steps",
            "tags",
        ),
        "events": (),
        "team_tags": (),
        "teams": (
            "experiments_categories",
            "experiments_status",
            "items_status",
            "teamgroups",
        ),
        "todolist": (),
        "unfinished_steps": (),
        "users": ("notifications",),
        "idps": (),
    }
    host = APIRequest.host

    def __init__(
        self,
        endpoint: str,
        unit_id: Union[int, str, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> None:
        self.endpoint = endpoint
        self.unit_id = unit_id
        self.sub_endpoint = sub_endpoint
        self.sub_unit_id = sub_unit_id
        self.query = query

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value: str):
        if value is not None:
            if value.lower() not in ElabFTWURL.VALID_ENDPOINTS.keys():
                raise ValueError(
                    f"Endpoint must be one of valid eLabFTW endpoints: {', '.join(ElabFTWURL.VALID_ENDPOINTS.keys())}"
                )
            self._endpoint = value
        else:
            self._endpoint = ""

    @property
    def sub_endpoint(self) -> str:
        return self._sub_endpoint

    @sub_endpoint.setter
    def sub_endpoint(self, value: str):
        if value is not None:
            if value.lower() not in ElabFTWURL.VALID_ENDPOINTS[self.endpoint]:
                raise ValueError(
                    f"A Sub-endpoint for endpoint '{self._endpoint}' must be "
                    f"one of valid eLabFTW sub-endpoints: {', '.join(ElabFTWURL.VALID_ENDPOINTS[self.endpoint])}"
                )
            self._sub_endpoint = value
        else:
            self._sub_endpoint = ""

    @property
    def unit_id(self) -> Union[int, str, None]:
        return self._unit_id

    @unit_id.setter
    def unit_id(self, value):
        if value is not None:
            if not re.match(r"^\w+$", value := str(value)):
                # Although, eLabFTW primarily supports integer-only IDs, there are exceptions, like the alias
                # ID "me" for receiving one's own user information.
                raise ValueError("Invalid unit ID (or entity ID)")
            self._unit_id = value
        else:
            self._unit_id = ""

    @property
    def sub_unit_id(self) -> Union[int, str, None]:
        return self._sub_unit_id

    @sub_unit_id.setter
    def sub_unit_id(self, value):
        if self.sub_endpoint is None:
            raise ValueError(
                "Sub-unit ID cannot be specified without specifying its sub-endpoint first."
            )
        if value is not None:
            if not re.match(r"^\w+$", value := str(value)):
                raise ValueError("Invalid sub-unit ID (or entity sub-ID)")
            self._sub_unit_id = value
        else:
            self._sub_unit_id = ""  # TODO: what an empty sub unit ID does

    @property
    def query(self) -> str:
        return self._query

    @query.setter
    def query(self, value: dict):
        self._query = "&".join([f"{k}={v}" for k, v in (value or dict()).items()])

    def get(self) -> str:
        url = (
            f"{ElabFTWURL.host}/{self.endpoint}/{self.unit_id}/"
            f"{self.sub_endpoint}/{self.sub_unit_id}"
        ).rstrip("/")
        if self.query:
            url += f"?{self.query}"
        return url


class GETRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        return super().client.get(url.get(), headers={"Accept": "application/json"})

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return super().__call__(endpoint, unit_id, sub_endpoint, sub_unit_id, query)


class POSTRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in (kwargs.pop("data", dict())).items()
        }
        files = kwargs.pop("files", None)
        return super().client.post(
            url.get(),
            headers={
                "Accept": "*/*",
                # If json argument isn't empty, '"Content-Type": "application/json"' is automatically set.
                # '"Content-Type": "multipart/form-data"', takes no effect, and
                # the server will return a 400 bad request.
                # See: https://blog.ian.stapletoncordas.co/2024/02/a-retrospective-on-requests
                # '"Content-Type": "application/json"' doesn't (and shouldn't) work when "files" isn't empty.
            },
            json=data,
            files=files,
            **kwargs,
        )

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return super().__call__(
            endpoint, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )


class AsyncPOSTRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(
            timeout=180,
            limits=Limits(
                max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
            ),
            **kwargs,
        )

    async def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in (kwargs.pop("data", dict())).items()
        }
        files = kwargs.pop("files", None)
        return await super().client.post(
            url.get(),
            headers={"Accept": "*/*"},
            json=data,
            files=files,
            **kwargs,
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        response = await self._make(
            endpoint, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )
        if not self.keep_session_open:
            await self.close()
        return response


class AsyncGETRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(
            timeout=180,
            limits=Limits(
                max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
            ),
            **kwargs,
        )

    async def _make(self, *args) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        return await super().client.get(
            url.get(),
            headers={"Accept": "application/json"},
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        response = await self._make(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        if not self.keep_session_open:
            await self.close()
        return response


class PATCHRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in kwargs.pop("data", dict()).items()
        }
        return super().client.patch(
            url.get(),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=data,
            **kwargs,
        )

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return super().__call__(
            endpoint, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )


class AsyncPATCHRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(
            timeout=180,
            limits=Limits(
                max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
            ),
            **kwargs,
        )

    async def _make(self, *args, **kwargs) -> Response:
        endpoint, unit_id, sub_endpoint, sub_unit_id, query = args
        url = ElabFTWURL(endpoint, unit_id, sub_endpoint, sub_unit_id, query)
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in kwargs.pop("data", dict()).items()
        }
        return await super().client.patch(
            url.get(),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=data,
            **kwargs,
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint: str,
        unit_id: Union[str, int, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        response = await self._make(
            endpoint, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )
        if not self.keep_session_open:
            await self.close()
        return response
