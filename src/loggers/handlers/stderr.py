import logging
from hashlib import md5

from src.loggers.handlers import Handler


class STDERRHandler(Handler):
    def __init__(self, suppress_stderr=False):
        self.suppress_stderr = suppress_stderr
        self.formatter: logging.Formatter = logging.Formatter(
            "%(levelname)s:%(filename)s: %(message)s"
        )

    def __eq__(self, other) -> bool:
        return super().__eq__(other)

    def __hash__(self) -> int:
        unique = self.formatter.__dict__.copy()
        unique.pop("_style")
        return int(md5(str(unique).encode("utf-8")).hexdigest(), base=16)

    @property
    def formatter(self) -> logging.Formatter:
        return self._formatter

    @formatter.setter
    def formatter(self, value=None):
        if not isinstance(value, logging.Formatter):
            raise ValueError("formatter must be a 'logging.Formatter' instance!")
        self._formatter = value

    @property
    def handler(self) -> logging.Handler:
        if self.suppress_stderr:
            import os

            handler = logging.FileHandler(filename=os.devnull)
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)
        handler.setLevel(logging.DEBUG)
        return handler

    @handler.setter
    def handler(self, value):
        raise AttributeError("'handler' cannot be modified!")
