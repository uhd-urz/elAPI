import logging
from hashlib import md5
from types import NoneType
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from ....styles import stderr_console
from .base import BaseHandler


class STDERRBaseHandler(BaseHandler):
    def __init__(
        self,
        formatter: logging.Formatter = logging.Formatter("%(message)s"),
        rich_level_colors: Optional[dict] = None,
    ):
        self.formatter: logging.Formatter = formatter
        self.rich_level_colors = rich_level_colors

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
    def rich_level_colors(self) -> dict[str, str]:
        return self._rich_level_colors

    @rich_level_colors.setter
    def rich_level_colors(self, value):
        if not isinstance(value, (NoneType, dict)):
            raise TypeError(
                "rich_level_colors must be None or a dictionary of log level "
                "names as keys and respective colors as values."
            )
        self._rich_level_colors = value

    def _get_rich_console(self) -> Console:
        if self.rich_level_colors is None:
            return stderr_console
        _rich_level_colors_for_console: dict = {}
        for level_name, color_name in self.rich_level_colors.items():
            _rich_level_colors_for_console[f"logging.level.{level_name}"] = color_name
        # Rich handler with colored level support:
        # https://github.com/Textualize/rich/issues/1161#issuecomment-813882224
        console = Console(theme=Theme(_rich_level_colors_for_console), stderr=True)
        return console

    @property
    def handler(self) -> logging.Handler:
        handler = RichHandler(
            show_time=False,
            enable_link_path=False,
            console=self._get_rich_console(),
        )
        handler.setFormatter(self.formatter)
        handler.setLevel(logging.INFO)
        return handler

    @handler.setter
    def handler(self, value):
        raise AttributeError("'handler' cannot be modified!")
