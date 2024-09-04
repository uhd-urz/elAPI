from functools import cached_property
from typing import Union, Iterable, Optional, Generator, Awaitable

from httpx import Response, AsyncClient, Client

from .api import (
    SimpleClient,
    GlobalSharedSession,
    GETRequest,
    POSTRequest,
    PATCHRequest,
    DELETERequest,
    AsyncGETRequest,
    AsyncPOSTRequest,
    AsyncPATCHRequest,
    AsyncDELETERequest,
)


class FixedAsyncEndpoint:
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self._is_global_shared_instance_none = GlobalSharedSession._instance is None

    @cached_property
    def _client(self) -> AsyncClient:
        return SimpleClient(is_async_client=True)

    @cached_property
    def _get_session(self) -> AsyncGETRequest:
        if self._is_global_shared_instance_none is False:
            return AsyncGETRequest()
        return AsyncGETRequest(shared_client=self._client)

    @cached_property
    def _post_session(self) -> AsyncPOSTRequest:
        if self._is_global_shared_instance_none is False:
            return AsyncPOSTRequest()
        return AsyncPOSTRequest(shared_client=self._client)

    @cached_property
    def _patch_session(self) -> AsyncPATCHRequest:
        if self._is_global_shared_instance_none is False:
            return AsyncPATCHRequest()
        return AsyncPATCHRequest(shared_client=self._client)

    @cached_property
    def _delete_session(self) -> AsyncDELETERequest:
        if self._is_global_shared_instance_none is False:
            return AsyncDELETERequest()
        return AsyncDELETERequest(shared_client=self._client)

    async def get(
        self,
        endpoint_id: Union[int, str, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return await self._get_session(
            self.endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )

    async def post(
        self,
        endpoint_id: Union[int, str, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await self._post_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    async def patch(
        self,
        endpoint_id: Union[int, str] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await self._patch_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    async def delete(
        self,
        endpoint_id: Union[int, str] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return await self._delete_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
        )

    async def aclose(self) -> Optional[type(NotImplemented)]:
        if self._is_global_shared_instance_none is False:
            await self._client.aclose()
        return NotImplemented


class FixedEndpoint:
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self._is_global_shared_instance_none = GlobalSharedSession._instance is None

    @cached_property
    def _client(self) -> Client:
        return SimpleClient(is_async_client=False)

    @cached_property
    def _get_session(self) -> GETRequest:
        if self._is_global_shared_instance_none is False:
            return GETRequest()
        return GETRequest(shared_client=self._client)

    @cached_property
    def _post_session(self) -> POSTRequest:
        if self._is_global_shared_instance_none is False:
            return POSTRequest()
        return POSTRequest(shared_client=self._client)

    @cached_property
    def _patch_session(self) -> PATCHRequest:
        if self._is_global_shared_instance_none is False:
            return PATCHRequest()
        return PATCHRequest(shared_client=self._client)

    @cached_property
    def _delete_session(self) -> DELETERequest:
        if self._is_global_shared_instance_none is False:
            return DELETERequest()
        return DELETERequest(shared_client=self._client)

    def get(
        self,
        endpoint_id: Union[int, str, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return self._get_session(
            self.endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )

    def post(
        self,
        endpoint_id: Union[int, str, None] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return self._post_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def patch(
        self,
        endpoint_id: Union[int, str] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return self._patch_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            **kwargs,
        )

    def delete(
        self,
        endpoint_id: Union[int, str] = None,
        sub_endpoint_name: Optional[str] = None,
        sub_endpoint_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return self._delete_session(
            self.endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
        )

    def close(self) -> Optional[type(NotImplemented)]:
        if self._is_global_shared_instance_none is False:
            self._client.close()
        return NotImplemented


class RecursiveGETEndpoint:
    def __init__(
        self,
        source: Iterable[dict],
        source_id_prefix: str,
        target_endpoint: FixedAsyncEndpoint,
    ):
        self.source = source
        self.source_id_prefix = source_id_prefix
        self.target_endpoint = target_endpoint

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        _error = TypeError("source must be an iterable of dictionaries!")
        try:
            _iter = iter(value)
        except TypeError:
            raise _error
        else:
            if not isinstance(next(_iter), dict):
                raise _error
            self._source = value

    @property
    def source_id_prefix(self):
        return self._source_id_prefix

    @source_id_prefix.setter
    def source_id_prefix(self, value):
        if not isinstance(value, str):
            raise TypeError("source_id_prefix must be a string!")
        self._source_id_prefix = value

    @property
    def target_endpoint(self):
        return self._target_endpoint

    @target_endpoint.setter
    def target_endpoint(self, value):
        if not isinstance(value, FixedAsyncEndpoint):
            raise TypeError(
                f"target_endpoint must be an instance of '{FixedAsyncEndpoint.__name__}'!"
            )
        self._target_endpoint = value

    def endpoints(self, **kwargs) -> Generator[Awaitable[Response], None, None]:
        for item in self.source:
            yield self.target_endpoint.get(
                endpoint_id=item[self.source_id_prefix], **kwargs
            )
