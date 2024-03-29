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


class ElabFTWURLError(Exception): ...


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
        endpoint_name: str,
        endpoint_id: Union[int, str, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> None:
        self.endpoint_name = endpoint_name
        self.endpoint_id = endpoint_id
        self.sub_endpoint_name = sub_endpoint_name
        self.sub_endpoint_id = sub_endpoint_id
        self.query = query

    @property
    def endpoint_name(self) -> str:
        return self._endpoint_name

    @endpoint_name.setter
    def endpoint_name(self, value: str):
        if value is not None:
            if value.lower() not in ElabFTWURL.VALID_ENDPOINTS.keys():
                raise ElabFTWURLError(
                    f"Endpoint must be one of valid eLabFTW endpoints: {', '.join(ElabFTWURL.VALID_ENDPOINTS.keys())}."
                )
            self._endpoint_name = value
        else:
            self._endpoint_name = ""

    @property
    def sub_endpoint_name(self) -> str:
        return self._sub_endpoint_name

    @sub_endpoint_name.setter
    def sub_endpoint_name(self, value: str):
        if value is not None:
            if value.lower() not in ElabFTWURL.VALID_ENDPOINTS[self.endpoint_name]:
                raise ElabFTWURLError(
                    f"A Sub-endpoint for endpoint '{self._endpoint_name}' must be "
                    f"one of valid eLabFTW sub-endpoints: {', '.join(ElabFTWURL.VALID_ENDPOINTS[self.endpoint_name])}."
                )
            self._sub_endpoint_name = value
        else:
            self._sub_endpoint_name = ""

    @property
    def endpoint_id(self) -> Union[int, str, None]:
        return self._endpoint_id

    @endpoint_id.setter
    def endpoint_id(self, value):
        if value is not None:
            if not re.match(r"^(\d+)$|^(me)$", value := str(value)):
                # Although, eLabFTW primarily supports integer-only IDs, there are exceptions, like the alias
                # ID "me" for receiving one's own user information.
                raise ElabFTWURLError("Invalid endpoint ID (or entity ID).")
            self._endpoint_id = value
        else:
            self._endpoint_id = ""

    @property
    def sub_endpoint_id(self) -> Union[int, str, None]:
        return self._sub_endpoint_id

    @sub_endpoint_id.setter
    def sub_endpoint_id(self, value):
        if self.sub_endpoint_name is None:
            raise ElabFTWURLError(
                "Sub-endpoint ID cannot be defined without first specifying its sub-endpoint name."
            )
        if value is not None:
            if not re.match(r"^(\d+)$|^(me)$", value := str(value)):
                raise ElabFTWURLError("Invalid sub-endpoint ID (or entity sub-ID).")
            self._sub_endpoint_id = value
        else:
            self._sub_endpoint_id = ""
            # Similar to an empty endpoint_id, an empty sub_endpoint_id sends back
            # the whole list of available resources for a given sub-endpoint as response.

    @property
    def query(self) -> str:
        return self._query

    @query.setter
    def query(self, value: dict):
        self._query = "&".join([f"{k}={v}" for k, v in (value or dict()).items()])

    def get(self) -> str:
        url = (
            f"{ElabFTWURL.host}/{self.endpoint_name}/{self.endpoint_id}/"
            f"{self.sub_endpoint_name}/{self.sub_endpoint_id}"
        ).rstrip("/")
        if self.query:
            url += f"?{self.query}"
        return url


class GETRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return super().client.get(url.get(), headers={"Accept": "application/json"})

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return super().__call__(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )


class POSTRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
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
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return super().__call__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
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
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
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
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        response = await self._make(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
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
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return await super().client.get(
            url.get(),
            headers={"Accept": "application/json"},
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        response = await self._make(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        if not self.keep_session_open:
            await self.close()
        return response


class PATCHRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in kwargs.pop("data", dict()).items()
        }
        return super().client.patch(
            url.get(),
            headers={
                "Accept": "application/json"
            },  # '"Content-Type": "application/json"' is passed automatically when json argument is passed.
            json=data,
            **kwargs,
        )

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return super().__call__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
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
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        data = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in kwargs.pop("data", dict()).items()
        }
        return await super().client.patch(
            url.get(),
            headers={"Accept": "application/json"},
            json=data,
            **kwargs,
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        response = await self._make(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )
        if not self.keep_session_open:
            await self.close()
        return response


class DELETERequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return super().client.delete(
            url.get(), headers={"Accept": "*/*", "Content-Type": "application/json"}
        )

    def close(self):
        super().close()

    def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return super().__call__(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )


class AsyncDELETERequest(APIRequest, is_async_client=True):
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
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return await super().client.delete(
            url.get(),
            headers={"Accept": "*/*", "Content-Type": "application/json"},
        )

    async def close(self):
        if not self.client.is_closed:
            await self.client.aclose()

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        response = await self._make(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        if not self.keep_session_open:
            await self.close()
        return response
