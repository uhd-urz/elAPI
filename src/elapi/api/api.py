import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Union, Optional, Tuple, Literal

import httpx._client as httpx_private_client_module
from httpx import Response, Client, AsyncClient, Limits
from httpx._types import AuthTypes
from httpx_auth import HeaderApiKey

from .. import APP_NAME, APP_BRAND_NAME
from ..configuration import (
    TOKEN_BEARER,
    get_active_host,
    get_active_api_token,
    get_active_enable_http2,
    get_active_verify_ssl,
    get_active_timeout,
)
from ..loggers import Logger
from ..styles import Missing
from ..utils import update_kwargs_with_defaults, get_app_version

USER_AGENT: str = (
    f"{APP_BRAND_NAME}/{get_app_version()} {httpx_private_client_module.USER_AGENT}"
)
httpx_private_client_module.USER_AGENT = USER_AGENT
logger = Logger()


@dataclass
class SessionDefaults:
    limits: Limits = field(
        default_factory=lambda: Limits(
            max_connections=100,
            max_keepalive_connections=20,
            # same as HTTPX default. The previous value "30" can be too much for the server when uvloop is used
            keepalive_expiry=60,
        )
    )


session_defaults = SessionDefaults()


class _CustomHeaderApiKey(HeaderApiKey): ...


class SimpleClient(httpx_private_client_module.BaseClient):
    def __new__(
        cls,
        *,
        is_async_client: bool,
        auth: Optional[AuthTypes] = _CustomHeaderApiKey(
            api_key=str(Missing()), header_name=TOKEN_BEARER
        ),
        **kwargs,
    ) -> Union[Client, AsyncClient]:
        from ..utils import check_reserved_keyword
        from .._names import CONFIG_FILE_NAME
        from ..configuration import (
            KEY_HOST,
            KEY_API_TOKEN,
            KEY_ENABLE_HTTP2,
            KEY_VERIFY_SSL,
            KEY_TIMEOUT,
            preventive_missing_warning,
        )

        host: str = get_active_host()
        api_token: str = get_active_api_token().token
        enable_http2 = get_active_enable_http2()
        verify_ssl = get_active_verify_ssl()
        timeout = get_active_timeout()

        if isinstance(auth, _CustomHeaderApiKey):
            auth.api_key = api_token
        for config_field in (
            (KEY_HOST, host),
            (KEY_API_TOKEN, api_token),
            (KEY_ENABLE_HTTP2, enable_http2),
            (KEY_VERIFY_SSL, verify_ssl),
            (KEY_TIMEOUT, timeout),
        ):
            preventive_missing_warning(config_field)
        client = Client if is_async_client is False else AsyncClient
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
                against=f"class {SimpleClient.__name__}, "
                f"so the parameter remains user-configurable "
                f"through {CONFIG_FILE_NAME} configuration file",
            )
            raise e


class GlobalSharedSession:
    _instance = None
    suppress_override_warning = False

    class _GlobalSharedSession:
        __slots__ = "_limited_to", "__dict__", "_kwargs"
        # __dict__ necessary for @cached_property

        def __init__(
            self, *, limited_to: Literal["sync", "async", "all"] = "all", **kwargs
        ):
            self.limited_to = limited_to.lower()
            self._kwargs = kwargs
            update_kwargs_with_defaults(self._kwargs, session_defaults.__dict__)

        @property
        def limited_to(self) -> str:
            return self._limited_to

        @limited_to.setter
        def limited_to(self, value: str):
            if value not in ("sync", "async", "all"):
                raise ValueError(
                    f"Given limited_to is '{value}', "
                    f"but it can only be 'sync', 'async', or 'all'."
                )
            self._limited_to = value

        @cached_property
        def sync_client(self) -> Optional[Client]:
            if self.limited_to in ("sync", "all"):
                return SimpleClient(is_async_client=False, **self._kwargs)
            return None

        @cached_property
        def async_client(self) -> Optional[AsyncClient]:
            if self.limited_to in ("async", "all"):
                return SimpleClient(is_async_client=True, **self._kwargs)
            return None

        def close(self) -> None:
            GlobalSharedSession._instance = None
            if self.sync_client is not None:
                if self.sync_client.is_closed is False:
                    self.sync_client.close()
            if self.async_client is not None:
                if self.async_client.is_closed is False:
                    # nest_asyncio is needed if there are multiple asyncio.run.
                    # ("RuntimeError: Event loop is closed").
                    try:
                        event_loop = asyncio.get_running_loop()
                    except RuntimeError:
                        asyncio.set_event_loop(event_loop := asyncio.new_event_loop())
                        try:
                            event_loop.run_until_complete(self.async_client.aclose())
                        except RuntimeError as e:
                            raise RuntimeError(
                                f"{GlobalSharedSession.__name__} has attempted to close {AsyncClient.__name__} "
                                f"{self.async_client} connection in a new event loop, because "
                                f"{GlobalSharedSession.__name__} could not find a running one. "
                                f"But it seems that failed as well. "
                                f"This likely means that either the event loop or "
                                f"{GlobalSharedSession.__name__} is being used incorrectly. "
                                f"Connection could not be closed. "
                                f"You can also try calling the 'close' method again."
                            ) from e
                        else:
                            event_loop.close()
                    else:
                        event_loop.create_task(self.async_client.aclose())

        def __enter__(self):
            self._outer_instance = GlobalSharedSession._instance
            # The instance is already created with __new__ by the time __enter__ is called
            return self._outer_instance

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._outer_instance.close()
            self._outer_instance = None

    def __new__(
        cls,
        *,
        limited_to: Literal["sync", "async", "all"] = "all",
        suppress_override_warning: bool = False,
        **kwargs,
    ):
        if cls._instance is None:
            cls.suppress_override_warning = suppress_override_warning
            cls._instance = cls._GlobalSharedSession(limited_to=limited_to, **kwargs)
        return cls._instance


class APIRequest(ABC):
    __slots__ = (
        "_shared_client",
        "_is_using_global_shared_session",
        "_kwargs",
        "__dict__",
    )

    def __init__(
        self,
        shared_client: Union[Client, AsyncClient, None] = None,
        **kwargs,
    ):
        update_kwargs_with_defaults(kwargs, session_defaults.__dict__)
        self._kwargs = kwargs
        if shared_client is not None:
            kwargs.update(shared_client=shared_client)
        self.is_global_shared_session_user = False
        self.shared_client = shared_client
        if (
            kwargs
            and kwargs != session_defaults.__dict__
            and self.is_global_shared_session_user is True
            and GlobalSharedSession.suppress_override_warning is False
        ):
            logger.warning(
                f"{self.__class__.__name__} received keyword arguments {kwargs} "
                f"while {GlobalSharedSession.__name__} is in use. "
                f"But {GlobalSharedSession.__name__} will override any argument "
                f"passed to {self.__class__.__name__}. You can pass the same arguments to"
                f"{GlobalSharedSession.__name__} instead. You can suppress this warning "
                f"by passing keyword argument 'suppress_override_warning = True' "
                f"to {GlobalSharedSession.__name__}."
            )

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, /, is_async_client: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.is_async_client = is_async_client

    @cached_property
    def client(self) -> Union[Client, AsyncClient]:
        if self.shared_client is not None:
            return self.shared_client
        return SimpleClient(is_async_client=self.is_async_client, **self._kwargs)

    @property
    def is_global_shared_session_user(self) -> bool:
        return self._is_using_global_shared_session

    @is_global_shared_session_user.setter
    def is_global_shared_session_user(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("is_using_global_shared_session value can only a bool!")
        self._is_using_global_shared_session = value

    @property
    def shared_client(self) -> Union[Client, AsyncClient]:
        return self._shared_client

    @shared_client.setter
    def shared_client(self, value: Union[Client, AsyncClient, None] = None):
        if not isinstance(value, (Client, AsyncClient, type(None))):
            raise TypeError(
                f"shared_client must be an instance of "
                f"httpx.{Client.__name__} or httpx.{AsyncClient.__name__} or {None}."
            )
        if self.is_async_client is True and isinstance(value, Client):
            raise ValueError(
                f"is_async_client is true, but value set to "
                f"shared_client is not an instance of httpx.{AsyncClient.__name__}!"
            )
        elif self.is_async_client is False and isinstance(value, AsyncClient):
            raise ValueError(
                f"is_async_client is not true, but value set to "
                f"shared_client is not an instance of httpx.{Client.__name__}!"
            )
        # noinspection PyProtectedMember
        if GlobalSharedSession._instance is not None:
            if self.is_async_client is False:
                if GlobalSharedSession().sync_client is not None:
                    self._shared_client = GlobalSharedSession().sync_client
                    self.is_global_shared_session_user = True
                else:
                    self._shared_client = None
                    self.is_global_shared_session_user = False
            else:
                if GlobalSharedSession().async_client is not None:
                    self._shared_client = GlobalSharedSession().async_client
                    self.is_global_shared_session_user = True
                else:
                    self._shared_client = None
                    self.is_global_shared_session_user = False
        else:
            self._shared_client = value

    @abstractmethod
    def _make(self, *args, **kwargs): ...

    @abstractmethod
    def close(self) -> Optional[type(NotImplemented)]:
        if self.is_global_shared_session_user is True:
            return NotImplemented
        if not self.client.is_closed:
            self.client.close()

    @abstractmethod
    async def aclose(self) -> Optional[type(NotImplemented)]:
        if self.is_global_shared_session_user is True:
            return NotImplemented
        if not self.client.is_closed:
            await self.client.aclose()

    @abstractmethod
    def __call__(self, *args, **kwargs):
        response = self._make(*args, **kwargs)
        if self.shared_client is None:
            self.close()
        return response

    @abstractmethod
    async def __acall__(self, *args, **kwargs):
        response = await self._make(
            *args,
            **kwargs,
        )
        if self.shared_client is None:
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
                    f"Endpoint must be one of valid eLabFTW endpoints: "
                    f"{', '.join(ElabFTWURL.VALID_ENDPOINTS.keys())}."
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
                    f"one of valid eLabFTW sub-endpoints: "
                    f"{', '.join(valid_sub_endpoint_name)}."
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
                # Although, eLabFTW primarily supports integer-only IDs,
                # there are exceptions, like the alias
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

    def close(self) -> Optional[type(NotImplemented)]:
        return super().close()

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

    def close(self) -> Optional[type(NotImplemented)]:
        return super().close()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    async def aclose(self) -> Optional[type(NotImplemented)]:
        return await super().aclose()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _make(self, *args, headers: Optional[dict] = None, **kwargs) -> Response:
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query = args
        url = ElabFTWURL(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
        return await super().client.get(
            url.get(), headers=headers or {"Accept": "application/json"}, **kwargs
        )

    async def aclose(self) -> Optional[type(NotImplemented)]:
        return await super().aclose()

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

    def close(self) -> Optional[type(NotImplemented)]:
        return super().close()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    async def aclose(self) -> Optional[type(NotImplemented)]:
        return await super().aclose()

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

    def close(self) -> Optional[type(NotImplemented)]:
        return super().close()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    async def aclose(self) -> Optional[type(NotImplemented)]:
        return await super().aclose()

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
