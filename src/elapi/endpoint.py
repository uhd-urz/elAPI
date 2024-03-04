from typing import Union, Iterable, Optional, Generator, Awaitable

from httpx import Response

from .api import (
    AsyncGETRequest,
    GETRequest,
    POSTRequest,
    PATCHRequest,
    AsyncPOSTRequest,
    AsyncPATCHRequest,
)


class FixedAsyncEndpoint:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self._get_session = AsyncGETRequest(keep_session_open=True)
        self._post_session = AsyncPOSTRequest(keep_session_open=True)
        self._patch_session = AsyncPATCHRequest(keep_session_open=True)

    async def get(
        self,
        unit_id: Union[int, str, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return await self._get_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query
        )

    async def post(
        self,
        unit_id: Union[int, str],
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await self._post_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )

    async def patch(
        self,
        unit_id: Union[int, str],
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return await self._patch_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )

    async def close(self):
        await self._get_session.close()
        await self._post_session.close()
        await self._patch_session.close()


class FixedEndpoint:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self._get_session = GETRequest(keep_session_open=True)
        self._post_session = POSTRequest(keep_session_open=True)
        self._patch_session = PATCHRequest(keep_session_open=True)

    def get(
        self,
        unit_id: Union[int, str, None] = None,
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
    ) -> Response:
        return self._get_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query
        )

    def post(
        self,
        unit_id: Union[int, str],
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return self._post_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )

    def patch(
        self,
        unit_id: Union[int, str],
        sub_endpoint: Optional[str] = None,
        sub_unit_id: Union[int, str, None] = None,
        query: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        return self._patch_session(
            self.unit_name, unit_id, sub_endpoint, sub_unit_id, query, **kwargs
        )

    def close(self):
        self._get_session.close()
        self._post_session.close()
        self._patch_session.close()


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
            yield self.target_endpoint.get(unit_id=item[self.source_id_prefix], **kwargs)
