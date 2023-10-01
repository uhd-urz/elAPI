import logging
from hashlib import md5

from src.loggers.handlers import Handler


class STDERRHandler(Handler):
    def __init__(self, suppress_stderr=False):
        self.suppress_stderr = suppress_stderr
        self.formatter: logging.Formatter = logging.Formatter(
            "%(levelname)s:%(filename)s: %(message)s"
        )

    def __eq__(self, other):
        super().__eq__(other)

    @property
    def formatter(self) -> logging.Formatter:
        return self._formatter

    @formatter.setter
    def formatter(self, value=None):
        if not isinstance(value, logging.Formatter):
            raise ValueError("formatter must be a 'logging.Formatter' instance!")
        self._formatter = value

    @property
    def handler(self):
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

    @property
    def unique(self):
        unique = self.formatter.__dict__.copy()
        unique.pop("_style")
        unique = str(unique).encode("utf-8")
        return md5(unique).hexdigest()
