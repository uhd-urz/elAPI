import logging
from hashlib import md5

from rich.logging import RichHandler

from . import Handler
from ...styles import stderr_console


class STDERRHandler(Handler):
    def __init__(self, suppress=False):
        self.suppress = suppress
        self.formatter: logging.Formatter = logging.Formatter("%(message)s")

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
        if self.suppress:
            import os

            handler = logging.FileHandler(filename=os.devnull)
        else:
            handler = RichHandler(
                show_time=False, enable_link_path=False, console=stderr_console
            )
        handler.setFormatter(self.formatter)
        handler.setLevel(logging.DEBUG)
        return handler

    @handler.setter
    def handler(self, value):
        raise AttributeError("'handler' cannot be modified!")
