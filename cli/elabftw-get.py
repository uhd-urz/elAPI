#!.venv/bin/python3

"""``elabftw-get`` script is a wrapper around an HTTP client (called ``httpx``). The goal is to be able to send API
queries from the command line following the API definitions from https://doc.elabftw.net/api/v2/ with ease. The script treats
API endpoints as the arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elabftw-get you can do the following:
        $ elabftw-get users <id>
"""
from src.defaults import HOST, API_TOKEN, TOKEN_BEARER
import httpx
from httpx_auth import HeaderApiKey
from rich import pretty
from rich.console import Console
import typer
from typing_extensions import Annotated
# noinspection PyProtectedMember
from src._doc import __PARAMETERS__doc__ as docs
# noinspection PyProtectedMember
from src._markdown_doc import _get_custom_help_text

# app = appeal.Appeal()
pretty.install()
console = Console(color_system="truecolor")
app = typer.Typer(rich_markup_mode="markdown")

typer.rich_utils.STYLE_HELPTEXT = ""  # fixes https://github.com/tiangolo/typer/issues/437
typer.rich_utils._get_help_text = _get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447


@app.command()
def main(endpoint: Annotated[str, typer.Argument(
    help=docs["endpoint"], show_default=False)],
         entity_id: Annotated[int, typer.Argument(help=docs["entity_id"])] = None,
         plaintext: Annotated[bool, typer.Option(help=docs["plaintext"], show_default=False)] = False) -> None:
    """
    Make HTTP API requests to elabftw's endpoints as documented in https://doc.elabftw.net/api/v2/.

    <br/>
    **Example**:
    <br/>
    From https://doc.elabftw.net/api/v2/#/Users/read-user:
    > GET /users/{id}

    With `elabftw-get` you can do the following:
    `$ elabftw-get users <id>`
    """

    with httpx.Client(auth=HeaderApiKey(api_key=f'{API_TOKEN}', header_name=TOKEN_BEARER),
                      verify=True) as client:
        response = client.get(f'{HOST}/{endpoint}/{entity_id}', headers={"Accept": "application/json"})
        # pretty_response = Syntax(response.text, "json")  # this only prints the first line!! Likely a rich bug.
        # rich.print_json(data)
        # alternative of console.print(). console.print() allows a little more customization through Console()
        console.print_json(response.text, indent=2) if not plaintext else print(response.json())


if __name__ == '__main__':
    app()
