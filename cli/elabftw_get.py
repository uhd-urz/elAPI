#!.venv/bin/python3

"""``elabftw-get`` script is a wrapper around an HTTP client (called ``httpx``). The goal is to be able to send API
queries from the command line following the API definitions from https://doc.elabftw.net/api/v2/ with ease.
The script treats API endpoints as its arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elabftw-get you can do the following:
        $ elabftw-get fetch users <id>
"""

import typer
from rich import pretty
from rich.console import Console
from rich.markdown import Markdown
from typing_extensions import Annotated

from cli._doc import __PARAMETERS__doc__ as docs
from cli._highlight_syntax import Highlight
from cli._markdown_doc import _get_custom_help_text

pretty.install()
console = Console(color_system="truecolor")
app = typer.Typer(rich_markup_mode="markdown", pretty_exceptions_show_locals=False)

typer.rich_utils.STYLE_HELPTEXT = ""  # fixes https://github.com/tiangolo/typer/issues/437
typer.rich_utils._get_help_text = _get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447


@app.command(short_help="Make `GET` requests to elabftw endpoints.")
def fetch(
        endpoint: Annotated[str, typer.Argument(
            help=docs["endpoint"], show_default=False)],
        unit_id: Annotated[str, typer.Option("--id", "-i", help=docs["unit_id_get"], show_default=False)] = None,
        output: Annotated[str, typer.Option("--output", "-o",
                                            help=docs["output"], show_default=False)]
        = "json"
) -> None:
    """
    Make `GET` requests to elabftw endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `GET users`](https://doc.elabftw.net/api/v2/#/Users/read-user),
    > GET /users/{id}

    With `elabftw-get` you can do the following:
    <br/>
    `$ elabftw-get fetch users` will return list of all users.
    <br/>
    `$ elabftw-get fetch users --id <id>` will return information about the specific user `<id>`.
    """
    from src import elabftw_fetch
    from src import Validate, ConfigValidator

    validate_config = Validate(ConfigValidator())
    validate_config()

    raw_response = elabftw_fetch(endpoint=endpoint, unit_id=unit_id)
    prettify = Highlight(data=raw_response.json(), lang=output)
    prettify.highlight()


@app.command(
    short_help="Make `POST` request to elabftw endpoints.",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True
    }
)
def post(
        endpoint: Annotated[str, typer.Argument(
            help=docs["endpoint"], show_default=False)], *,
        unit_id: Annotated[str, typer.Option("--id", "-i", help=docs["unit_id_post"], show_default=False)] = None,
        json_: Annotated[str, typer.Option("--data", "-d", help=docs["data"], show_default=False)] = None,
        data: typer.Context = None,
        output: Annotated[str, typer.Option("--output", "-o",
                                            help=docs["output"], show_default=False)]
        = "json"
) -> None:
    """
    Make `POST` request to elabftw endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `POST users`](https://doc.elabftw.net/api/v2/#/Users/post-user),
    > POST /users/{id}

    With `elabftw-get` you can do the following:
    <br/>
    `$ elabftw-get post users --firstname John --lastname Doe --email "john_doe@email.com"` will create a new user.
    """
    import ast
    from src import elabftw_post
    from json import JSONDecodeError
    from src import Validate, ConfigValidator

    validate_config = Validate(ConfigValidator())
    validate_config()

    if json_:
        valid_data: dict = ast.literal_eval(json_)
    else:
        data_keys: list[str, ...] = [_.removeprefix("--") for _ in data.args[::2]]
        data_values: list[str, ...] = data.args[1::2]
        valid_data: dict[str: str, ...] = dict(zip(data_keys, data_values))
    raw_response = elabftw_post(endpoint, unit_id=unit_id, **valid_data)
    try:
        prettify = Highlight(data=raw_response.json(), lang=output)
    except JSONDecodeError:
        if raw_response.is_success:
            console.print("Success: Resource created!", style="green")
        else:
            console.print(f"Warning: Something unexpected happened! "
                          f"The HTTP return was '{raw_response}'.", style="red")
    else:
        prettify.highlight()


@app.command(name="show-config")
def show_config() -> None:
    """
    Get information about detected configuration values.
    """
    from apps.show_config import info

    md = Markdown(info)
    console.print(md)


@app.command()
def cleanup() -> None:
    """
    Remove cached data.
    """
    from src import ProperPath, TMP_DIR

    ProperPath(TMP_DIR).remove(output_handler=console.print)
    console.print("Done!")


@app.command(name="bill-teams")
def bill_teams(output: Annotated[str, typer.Option("--output", "-o",
                                                   help=docs["output"], show_default=False)] = "json") -> None:
    """*Beta:* Generate billable teams data."""
    from src import Validate, ConfigValidator, PermissionValidator

    validate = Validate(ConfigValidator(), PermissionValidator("sysadmin"))
    validate()

    from apps.bill_teams import get_team_owners

    billable = get_team_owners()
    prettify = Highlight(data=billable, lang=output)
    prettify.highlight()


if __name__ == '__main__':
    app()
