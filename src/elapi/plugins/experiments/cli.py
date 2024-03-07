import typer

from ...cli.helpers import OrderedCommands
from ...loggers import Logger

logger = Logger()


app = typer.Typer(
    cls=OrderedCommands,
    rich_markup_mode="markdown",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)
