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
    SUPPORTED_FORMAT: ClassVar[dict] = {"JSON": r"json", "YAML": r"ya?ml", "text": r"(plain)?text"}
    console: ClassVar[Console] = Console(color_system="truecolor")
    data: Union[dict, str]
    lang: str = "json"
    theme: str = "lightbulb"

    def __post_init__(self):
        self.language = self.lang

    @property
    def language(self):
        return self.lang

    @language.setter
    def language(self, value):
        if not re.match(r"|".join(Highlight.SUPPORTED_FORMAT.values()), value, flags=re.IGNORECASE):
            logger.error(f"The provided format '{value}' cannot be highlighted! "
                         f"Supported formats are: JSON, YAML, plaintext.")
            print("\n", file=sys.stderr)
            self.lang = "text"  # falls back to "text"
        else:
            self.lang = value

    def get_syntax(self, data):
        return Syntax(data, self.language, background_color="default", theme=self.theme)

    @property
    def format(self):
        if re.match(Highlight.SUPPORTED_FORMAT["JSON"], self.language, flags=re.IGNORECASE):
            return json.dumps(self.data, indent=True, ensure_ascii=True)

        elif re.match(Highlight.SUPPORTED_FORMAT["YAML"], self.language, flags=re.IGNORECASE):
            return yaml.dump(self.data)

        else:
            return self.data

    @format.setter
    def format(self, value):
        raise AttributeError("format is stored internally. It cannot be modified!")

    def highlight(self):
        formatted = self.format
        if re.match(Highlight.SUPPORTED_FORMAT["text"], self.language, flags=re.IGNORECASE):
            print(self.data)
        else:
            highlighted = self.get_syntax(data=formatted)
            Highlight.console.print(highlighted)
