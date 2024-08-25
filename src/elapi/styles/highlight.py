from abc import ABC, abstractmethod
from typing import Any

from colorama import Fore
from rich.padding import Padding
from rich.syntax import Syntax
from rich.text import Text

from .formats import RegisterFormattingLanguage


class BaseHighlight(ABC):
    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        return issubclass(subclass, Syntax) or super().__subclasshook__(cls, subclass)

    @abstractmethod
    def __call__(self, *args, **kwargs): ...


class Highlight(BaseHighlight):
    def __init__(self, language: str, /, theme: str = "lightbulb", *, package_identifier: str):
        validator = RegisterFormattingLanguage(language, package_identifier=package_identifier)
        self.name = validator.name
        self.theme = theme

    def __call__(self, data: str) -> Syntax:
        return Syntax(
            data,
            self.name,
            background_color="default",
            theme=self.theme,
            word_wrap=True,
        )


class NoteText:
    def __new__(
        cls, text: str, /, stem: str = "P.S.", color: str = "yellow", indent: int = 3
    ):
        return Padding(
            f"{Text(f'[b {color}]{stem}:[/b {color}]')} {text}", pad=(1, 0, 0, indent)
        )


class ColorText:
    def __init__(self, text: Any, /):
        self.text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not hasattr(value, "__str__"):
            raise TypeError(
                "text value must be an object that implements '__str__' attribute!"
            )
        self._text = str(value)

    def colorize(self, ansi_color: str) -> str:
        return f"{ansi_color}{self.text}{Fore.RESET}"


def print_typer_error(error_message: str) -> None:
    import click
    from typer.rich_utils import rich_format_error

    exception = click.ClickException(error_message)
    exception.ctx = click.get_current_context()
    rich_format_error(exception)
