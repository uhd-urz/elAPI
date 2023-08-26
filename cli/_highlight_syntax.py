import json
import re
import sys
from dataclasses import dataclass
from functools import partial
from typing import ClassVar, Union

import yaml
from rich.console import Console
from rich.syntax import Syntax

from src import logger


@dataclass
class Highlight:
    # SUPPORTED_FORMAT contains the definitions for parsers that will parse and format the JSON from HTTP response.
    # Though not the most common practice (there's no protection against modifying "TEXT": {...} (the fallback format),
    # this design allows for adding support for a new format quite easily.
    SUPPORTED_FORMAT: ClassVar[dict] = {
        "JSON": {
            "pattern": r"json",
            "parser": partial(json.dumps, indent=True, ensure_ascii=True)

        },
        "YAML": {
            "pattern": r"ya?ml",
            "parser": partial(yaml.dump, allow_unicode=True)
        },
        "PLAINTEXT": {
            "pattern": r"(plain)?text",
            "parser": lambda data: data
        }
    }
    _FALLBACK_FORMAT: ClassVar[str] = "PLAINTEXT"
    console: ClassVar[Console] = Console(color_system="truecolor")
    data: Union[dict, str]
    lang: str = "JSON"
    theme: str = "lightbulb"

    def __post_init__(self) -> None:
        self.language = self.lang

    @property
    def language(self) -> str:
        return self.lang

    @language.setter
    def language(self, value: str) -> None:
        for key in Highlight.SUPPORTED_FORMAT:
            if re.match(Highlight.SUPPORTED_FORMAT[key]["pattern"], value, flags=re.IGNORECASE):
                self.lang = key
                break

        if self.lang not in Highlight.SUPPORTED_FORMAT:
            logger.error(f"The provided format '{value}' cannot be highlighted! "
                         f"Supported formats are: {Highlight.SUPPORTED_FORMAT.keys()}")
            print("\n", file=sys.stderr)
            self.lang = Highlight._FALLBACK_FORMAT  # falls back to "PLAINTEXT"

    def get_syntax(self, data: str) -> Syntax:
        # If data is str but un-formatted (without new lines or indentations), rich will not try to format it of course,
        # which will result in a highlighted but an ultra-compact single line output!
        # E.g., if data = response.text or json.dump(data) (no indentation)
        return Syntax(data, self.language, background_color="default", theme=self.theme)

    @property
    def format(self) -> Union[str, dict]:
        return Highlight.SUPPORTED_FORMAT[self.language]["parser"](self.data)

    @format.setter
    def format(self, value) -> None:
        raise AttributeError("format is stored internally. It cannot be modified!")

    def highlight(self) -> None:
        formatted = self.format
        if self.language == Highlight._FALLBACK_FORMAT:
            print(formatted)
        else:
            highlighted = self.get_syntax(data=formatted)
            Highlight.console.print(highlighted)
