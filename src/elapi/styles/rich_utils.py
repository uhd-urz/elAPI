from typing import Union, Callable, Optional

import click
from typer.core import MarkupMode
from typer.rich_utils import rich_format_help


def rich_format_help_with_callback(
    *,
    obj: Union[click.Command, click.Group],
    ctx: click.Context,
    markup_mode: MarkupMode,
    result_callback: Optional[Callable] = None,
) -> None:
    rich_format_help(obj=obj, ctx=ctx, markup_mode=markup_mode)
    if result_callback is not None:
        result_callback()
