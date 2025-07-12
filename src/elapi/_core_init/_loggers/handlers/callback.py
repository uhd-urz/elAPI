from logging import Handler

from .base import LogRecordContainer


class ResultCallbackHandler(Handler):
    _client_count: int = 0
    _store_okay: bool = False

    def __init__(self):
        super().__init__()
        self.log_container = LogRecordContainer()

    @classmethod
    def enable_store_okay(cls) -> None:
        cls._store_okay = True
        cls._client_count += 1

    @classmethod
    def is_store_okay(cls) -> bool:
        return cls._store_okay

    @classmethod
    def get_client_count(cls) -> int:
        return cls._client_count

    def emit(self, record):
        if self._store_okay:
            self.log_container.append(record)
