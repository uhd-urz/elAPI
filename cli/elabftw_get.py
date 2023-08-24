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

import httpx
import typer
from httpx import Response
from httpx_auth import HeaderApiKey
from rich import pretty
from rich.console import Console
from rich.markdown import Markdown
from typing_extensions import Annotated

from apps.debug_info import info
from cli._doc import __PARAMETERS__doc__ as docs
from cli._markdown_doc import _get_custom_help_text
from src import HOST, API_TOKEN, TOKEN_BEARER, ProperPath, TMP_DIR

# app = appeal.Appeal()
pretty.install()
console = Console(color_system="truecolor")
app = typer.Typer(rich_markup_mode="markdown")

typer.rich_utils.STYLE_HELPTEXT = ""  # fixes https://github.com/tiangolo/typer/issues/437
typer.rich_utils._get_help_text = _get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447


def elabftw_response(endpoint: str, unit_id: int = None) -> Response:
    with httpx.Client(auth=HeaderApiKey(api_key=API_TOKEN, header_name=TOKEN_BEARER), verify=True) as client:
        response = client.get(f'{HOST}/{endpoint}/{unit_id}', headers={"Accept": "application/json"})
    return response


@app.command()
def fetch(endpoint: Annotated[str, typer.Argument(
    help=docs["endpoint"], show_default=False)],
          unit_id: Annotated[int, typer.Argument(help=docs["unit_id"])] = None,
          plaintext: Annotated[bool, typer.Option("--plaintext", "-p",
                                                  help=docs["plaintext"], show_default=False)] = False) -> None:
    """
    Make HTTP API requests to elabftw's endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/)

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `GET users`](https://doc.elabftw.net/api/v2/#/Users/read-user),
    > GET /users/{id}

    With `elabftw-get` you can do the following:
    `$ elabftw-get fetch users <id>`
    """

    raw_response = elabftw_response(endpoint=endpoint, unit_id=unit_id)

    # pretty_response = Syntax(response.text, "json")  # this only prints the first line!! Likely a rich bug.
    # rich.print_json(data)
    # alternative of console.print(). console.print() allows a little more customization through Console()

    console.print_json(raw_response.text, indent=2) if not plaintext else print(raw_response.json())


@app.command(name="show-config")
def show_config():
    """
    Get information about detected configuration values.
    """
    md = Markdown(info)
    console.print(md)


@app.command()
def cleanup():
    """
    Remove cached data
    """
    ProperPath(TMP_DIR).remove(output_handler=console.print)
    console.print(f"Done!")


if __name__ == '__main__':
    app()
