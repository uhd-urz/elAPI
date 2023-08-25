import json
import re
import sys
from dataclasses import dataclass
from typing import ClassVar, Union

import yaml
from rich.console import Console
from rich.syntax import Syntax

from src import logger


@dataclass
class Highlight:
    SUPPORTED_FORMAT: ClassVar[dict] = {
        "JSON": {
            "pattern": r"json",
            "parser": lambda data: json.dumps(data, indent=True, ensure_ascii=True)
        },
        "YAML": {
            "pattern": r"ya?ml",
            "parser": lambda data: yaml.dump(data)
        },
        "TEXT": {
            "pattern": r"(plain)?text",
            "parser": lambda data: data
        }
    }
    FALLBACK_FORMAT: ClassVar[str] = "TEXT"
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
    def language(self, value) -> None:
        for key in Highlight.SUPPORTED_FORMAT:
            if re.match(Highlight.SUPPORTED_FORMAT[key]["pattern"], value, flags=re.IGNORECASE):
                self.lang = key
                break

        if self.lang not in Highlight.SUPPORTED_FORMAT:
            logger.error(f"The provided format '{value}' cannot be highlighted! "
                         f"Supported formats are: {Highlight.SUPPORTED_FORMAT.keys()}")
            print("\n", file=sys.stderr)
            self.lang = Highlight.FALLBACK_FORMAT  # falls back to "text"

    def get_syntax(self, data) -> Syntax:
        return Syntax(data, self.language, background_color="default", theme=self.theme)

    @property
    def format(self) -> Union[str, dict]:
        return Highlight.SUPPORTED_FORMAT[self.language]["parser"](self.data)

    @format.setter
    def format(self, value) -> None:
        raise AttributeError("format is stored internally. It cannot be modified!")

    def highlight(self) -> None:
        formatted = self.format
        if self.language == Highlight.FALLBACK_FORMAT:
            print(formatted)
        else:
            highlighted = self.get_syntax(data=formatted)
            Highlight.console.print(highlighted)
