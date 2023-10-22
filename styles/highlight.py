from abc import ABC, abstractmethod

from rich.padding import Padding
from rich.syntax import Syntax
from rich.text import Text

from styles.format import ValidateLanguage


class BaseHighlight(ABC):
    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        return issubclass(subclass, Syntax) or super().__subclasshook__(cls, subclass)

    @abstractmethod
    def __call__(self, *args, **kwargs):
        ...


class Highlight(BaseHighlight):
    def __init__(self, language: str, /, theme: str = "lightbulb"):
        validator = ValidateLanguage(language)
        self.name = validator.name
        self.theme = theme

    def __call__(self, data: str) -> Syntax:
        return Syntax(data, self.name, background_color="default", theme=self.theme)


class NoteText:
    def __new__(
        cls, text: str, /, stem: str = "P.S.", color: str = "yellow", indent: int = 3
    ):
        return Padding(
            f"{Text(f'[b {color}]{stem}:[/b {color}]')} {text}", pad=(1, 0, 0, indent)
        )
