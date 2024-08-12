import re
from abc import ABC, abstractmethod
from typing import Union, Optional, Tuple

from httpx import Response, Client, AsyncClient, Limits
from httpx._client import BaseClient
from httpx._types import AuthTypes
from httpx_auth import HeaderApiKey

from .. import APP_NAME
from ..configuration import (
    TOKEN_BEARER,
    get_active_host,
    get_active_api_token,
    get_active_enable_http2,
    get_active_verify_ssl,
    get_active_timeout,
)
from ..styles import Missing


class _CustomHeaderApiKey(HeaderApiKey): ...


class CustomClient(BaseClient):
    def __new__(
        cls,
        *,
        is_async_client: bool = False,
        auth: Optional[AuthTypes] = _CustomHeaderApiKey(
            api_key=str(Missing()), header_name=TOKEN_BEARER
        ),
        **kwargs,
    ) -> Union[Client, AsyncClient]:
        from ..utils import check_reserved_keyword
        from .._names import CONFIG_FILE_NAME
        from ..utils import missing_warning
        from ..configuration import (
            KEY_HOST,
            KEY_API_TOKEN,
            KEY_ENABLE_HTTP2,
            KEY_VERIFY_SSL,
            KEY_TIMEOUT,
        )

        host: str = get_active_host()
        api_token: str = get_active_api_token().token
        enable_http2 = get_active_enable_http2()
        verify_ssl = get_active_verify_ssl()
        timeout = get_active_timeout()

        if isinstance(auth, _CustomHeaderApiKey):
            auth.api_key = api_token
        for field in (
            (KEY_HOST, host),
            (KEY_API_TOKEN, api_token),
            (KEY_ENABLE_HTTP2, enable_http2),
            (KEY_VERIFY_SSL, verify_ssl),
            (KEY_TIMEOUT, timeout),
        ):
            missing_warning(field)
        client = Client if not is_async_client else AsyncClient
        try:
            return client(
                auth=auth,
                http2=enable_http2,
                verify=verify_ssl,
                timeout=timeout,
                **kwargs,
            )
        except TypeError as e:
            check_reserved_keyword(
                e,
                what=f"{APP_NAME}",
                against=f"class {CustomClient.__name__}, "
                f"so the parameter remains user-configurable "
                f"through {CONFIG_FILE_NAME} configuration file",
            )
            raise e


class APIRequest(ABC):
    __slots__ = "keep_session_open", "_client"

    def __init__(self, keep_session_open: bool = False, **kwargs):
        self.keep_session_open = keep_session_open
        self._client: Union[Client, AsyncClient] = CustomClient(
            is_async_client=self.is_async_client, **kwargs
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
    async def aclose(self):
        if not self.client.is_closed:
            await self.client.aclose()

    @abstractmethod
    def __call__(self, *args, **kwargs):
        response = self._make(*args, **kwargs)
        if not self.keep_session_open:
            self.close()
        return response

    @abstractmethod
    async def __acall__(self, *args, **kwargs):
        response = await self._make(
            *args,
            **kwargs,
        )
        if not self.keep_session_open:
            await self.aclose()
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
            "tags",
        ),
        "todolist": (),
        "unfinished_steps": (),
        "users": ("notifications", "uploads"),
        "idps": (),
        "import": (),
        "exports": (),
    }

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
    def host(self) -> str:
        return get_active_host()

    @host.setter
    def host(self, value):
        raise AttributeError("Host value cannot be modified!")

    @host.deleter
    def host(self):
        raise AttributeError("Host cannot be deleted!")

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
            if value.lower() not in (
                valid_sub_endpoint_name := ElabFTWURL.VALID_ENDPOINTS[
                    self.endpoint_name
                ]
            ):
                if not valid_sub_endpoint_name:
                    raise ElabFTWURLError(
                        f"Endpoint '{self._endpoint_name}' does not have any sub-endpoint!"
                    )

                raise ElabFTWURLError(
                    f"A Sub-endpoint for endpoint '{self._endpoint_name}' must be "
                    f"one of valid eLabFTW sub-endpoints: {', '.join(valid_sub_endpoint_name)}."
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
            if not re.match(r"^(\d+)$|^(me)$|^(current)$", value := str(value)):
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
            if not re.match(r"^(\d+)$|^(me)$|^(current)$", value := str(value)):
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
            f"{self.host}/{self.endpoint_name}/{self.endpoint_id}/"
            f"{self.sub_endpoint_name}/{self.sub_endpoint_id}"
        ).rstrip("/")
        if self.query:
            url += f"?{self.query}"
        return url


class GETRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return super().client.get(
            url.get(), headers=headers or {"Accept": "application/json"}, **kwargs
        )

    def close(self):
        super().close()

    def aclose(self):
        raise NotImplementedError(
            f"{GETRequest.__name__} is not async and only supports 'close' method."
        )

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

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class POSTRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
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
            headers=headers
            or {
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

    def aclose(self):
        raise NotImplementedError(
            f"{POSTRequest.__name__} is not async and only supports 'close' method."
        )

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

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class AsyncPOSTRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(
        self,
        limits=Limits(
            max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
        ),
        **kwargs,
    ):
        super().__init__(
            limits=limits,
            **kwargs,
        )

    async def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
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
            headers=headers or {"Accept": "*/*"},
            json=data,
            files=files,
            **kwargs,
        )

    async def aclose(self):
        await super().aclose()

    def close(self):
        raise NotImplementedError(
            f"{AsyncPOSTRequest.__name__} is async and only supports 'aclose' method."
        )

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await super().__acall__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class AsyncGETRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(
        self,
        limits=Limits(
            max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
        ),
        **kwargs,
    ):
        super().__init__(
            limits=limits,
            **kwargs,
        )

    async def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return await super().client.get(
            url.get(), headers=headers or {"Accept": "application/json"}, **kwargs
        )

    async def aclose(self):
        if not self.client.is_closed:
            await self.client.aclose()

    def close(self):
        raise NotImplementedError(
            f"{AsyncGETRequest.__name__} is async and only supports 'aclose' method."
        )

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await super().__acall__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class PATCHRequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
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
            headers=headers
            or {
                "Accept": "application/json"
            },  # '"Content-Type": "application/json"' is passed automatically when json argument is passed.
            json=data,
            **kwargs,
        )

    def close(self):
        super().close()

    def aclose(self):
        raise NotImplementedError(
            f"{PATCHRequest.__name__} is not async and only supports 'close' method."
        )

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

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class AsyncPATCHRequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(
        self,
        limits=Limits(
            max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
        ),
        **kwargs,
    ):
        super().__init__(
            limits=limits,
            **kwargs,
        )

    async def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
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
            headers=headers or {"Accept": "application/json"},
            json=data,
            **kwargs,
        )

    async def aclose(self):
        if not self.client.is_closed:
            await self.client.aclose()

    def close(self):
        raise NotImplementedError(
            f"{AsyncPATCHRequest.__name__} is async and only supports 'aclose' method."
        )

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await super().__acall__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class DELETERequest(APIRequest):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return super().client.delete(
            url.get(),
            headers=headers or {"Accept": "*/*", "Content-Type": "application/json"},
            **kwargs,
        )

    def close(self):
        super().close()

    def aclose(self):
        raise NotImplementedError(
            f"{DELETERequest.__name__} is not async and only supports 'close' method."
        )

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

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )


class AsyncDELETERequest(APIRequest, is_async_client=True):
    __slots__ = ()

    def __init__(
        self,
        limits=Limits(
            max_connections=100, max_keepalive_connections=30, keepalive_expiry=60
        ),
        **kwargs,
    ):
        super().__init__(
            limits=limits,
            **kwargs,
        )

    async def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return await super().client.delete(
            url.get(),
            headers=headers or {"Accept": "*/*", "Content-Type": "application/json"},
            **kwargs,
        )

    async def aclose(self):
        if not self.client.is_closed:
            await self.client.aclose()

    def close(self):
        raise NotImplementedError(
            f"{AsyncDELETERequest.__name__} is async and only supports 'aclose' method."
        )

    async def __call__(
        self,
        endpoint_name: str,
        endpoint_id: Union[str, int, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await super().__acall__(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def __acall__(self, *args, **kwargs):
        raise NotImplementedError(
            "__acall__ cannot be called directly. It's mainly an async"
            " placeholder for __call__. Please use __call__ instead."
        )
