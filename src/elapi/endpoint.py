from typing import Union, Iterable

from .api import AsyncGETRequest


class FixedEndpoint:
    def __init__(self, unit_name: str, keep_session_open: bool = False):
        self.unit_name = unit_name
        self._session = AsyncGETRequest(keep_session_open=keep_session_open)

    @property
    def session(self) -> AsyncGETRequest:
        return self._session

    @session.setter
    def session(self, value):
        raise AttributeError("Session cannot be modified!")

    @property
    def DATA_FORMAT(self):
        return "json"

    async def json(self, unit_id: Union[str, int, None] = None, **kwargs) -> dict:
        response = await self.session(self.unit_name, unit_id)
        return response.json(**kwargs)


class RecursiveEndpoint:
    def __init__(
        self,
        source: Iterable[dict],
        source_id_prefix: str,
        target_endpoint: FixedEndpoint,
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
        if not isinstance(value, FixedEndpoint):
            raise TypeError("target_endpoint must be an instance of FixedEndpoint!")
        self._target_endpoint = value

    def items(self):
        for item in self.source:
            yield self.target_endpoint.json(unit_id=item[self.source_id_prefix])
