#!.venv/bin/python3

"""``elapi`` script is a wrapper around an HTTP client (called ``httpx``). The goal is to be able to send API
queries from the command line following the API definitions from https://doc.elabftw.net/api/v2/ with ease.
The script treats API endpoints as its arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elapi you can do the following:
        $ elapi fetch users <id>
"""
from typing import Optional

import typer
from rich import pretty
from rich.console import Console
from rich.markdown import Markdown
from typing_extensions import Annotated

from cli._doc import __PARAMETERS__doc__ as docs
from cli._markdown_doc import _get_custom_help_text
from src import APP_NAME
from src.loggers import Logger
from src.path import ProperPath

logger = Logger()


pretty.install()
console = Console(color_system="truecolor")
app = typer.Typer(rich_markup_mode="markdown", pretty_exceptions_show_locals=False)

typer.rich_utils.STYLE_HELPTEXT = (
    ""  # fixes https://github.com/tiangolo/typer/issues/437
)
typer.rich_utils._get_help_text = (
    _get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447
)


class _CLIExport:
    def __new__(cls, output: Optional[str] = None, export_dest: str = None):
        from collections import namedtuple
        from src.validators import Validate
        from cli._export import ExportValidator

        validate_export = Validate(ExportValidator(export_dest))
        export_dest: ProperPath = validate_export.get()

        _export_file_ext: str = (
            export_dest.expanded.suffix.removeprefix(".")
            if export_dest.kind == "file"
            else None
        )
        output = output or _export_file_ext or "json"  # default output format
        ExportParams = namedtuple(
            "ExportParams", ["output", "destination", "extension"]
        )
        return ExportParams(output, export_dest, _export_file_ext)


class _CLIFormat:
    def __new__(cls, output: Optional[str], export_file_ext: Optional[str] = None):
        from cli._format import Format

        try:
            format = Format(output)
        except ValueError as e:
            logger.error(e)
            logger.info(f"{APP_NAME} will fallback to 'txt' format.")
            format = Format("txt")  # Falls back to "txt"
        if export_file_ext and format.name != export_file_ext:
            logger.info(
                f"File extension is '{export_file_ext}' but data format will be '{format.name}'."
            )
        return format


@app.command(short_help="Make `GET` requests to elabftw endpoints.")
def get(
    endpoint: Annotated[str, typer.Argument(help=docs["endpoint"], show_default=False)],
    unit_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["unit_id_get"], show_default=False)
    ] = None,
    output: Annotated[
        Optional[str],
        typer.Option("--output", "-o", help=docs["output"], show_default=False),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["export"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[str, typer.Argument(hidden=True)] = None,
) -> None:
    """
    Make `GET` requests to elabftw endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `GET users`](https://doc.elabftw.net/api/v2/#/Users/read-user),
    > GET /users/{id}

    With `elapi` you can do the following:
    <br/>
    `$ elapi fetch users` will return list of all users.
    <br/>
    `$ elapi fetch users --id <id>` will return information about the specific user `<id>`.
    """
    from src.api import GETRequest
    from src.validators import Validate, HostIdentityValidator
    from cli._export import Export
    from cli._format import Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    output, export_dest, export_file_ext = _CLIExport(output, _export_dest)
    format = _CLIFormat(output, export_file_ext)

    session = GETRequest()
    raw_response = session(endpoint, unit_id)

    formatted_data = format(raw_response.json())

    if export:
        file_name_prefix = f"{endpoint}_{unit_id}" if unit_id else f"{endpoint}"
        export = Export(
            export_dest,
            file_name_prefix=file_name_prefix,
            file_extension=format.name,
        )
        export(data=formatted_data)
        console.print(export.success_message)
    else:
        highlight = Highlight(output)
        console.print(highlight(formatted_data))


@app.command(
    short_help="Make `POST` request to elabftw endpoints.",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def post(
    endpoint: Annotated[str, typer.Argument(help=docs["endpoint"], show_default=False)],
    *,
    unit_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["unit_id_post"], show_default=False)
    ] = None,
    json_: Annotated[
        str, typer.Option("--data", "-d", help=docs["data"], show_default=False)
    ] = "",
    data: typer.Context = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help=docs["output"], show_default=False)
    ] = "json",
) -> None:
    """
    Make `POST` request to elabftw endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `POST users`](https://doc.elabftw.net/api/v2/#/Users/post-user),
    > POST /users/{id}

    With `elapi` you can do the following:
    <br/>
    `$ elapi post users --firstname John --lastname Doe --email "john_doe@email.com"` will create a new user.
    """
    import ast
    from src.api import POSTRequest
    from json import JSONDecodeError
    from src.validators import Validate, HostIdentityValidator
    from cli._format import Format, Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if json_:
        valid_data: dict = ast.literal_eval(json_)
    else:
        data_keys: list[str, ...] = [_.removeprefix("--") for _ in data.args[::2]]
        data_values: list[str, ...] = data.args[1::2]
        valid_data: dict[str:str, ...] = dict(zip(data_keys, data_values))
    session = POSTRequest()
    raw_response = session(endpoint, unit_id, **valid_data)
    format = Format(output)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            console.print("Success: Resource created!", style="green")
        else:
            console.print(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was '{raw_response}'.",
                style="red",
            )
    else:
        highlight = Highlight(output)
        console.print(highlight(formatted_data))


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
    from src.configuration import TMP_DIR
    from src.path import ProperPath
    from time import sleep

    with console.status("Cleaning up...", refresh_per_second=15):
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        ProperPath(TMP_DIR, err_logger=logger).remove(verbose=True)
    console.print("Done!", style="green")


@app.command(name="bill-teams")
def bill_teams(
    is_async_client: Annotated[
        Optional[bool],
        typer.Option("--async", "-a", help=docs["async"], show_default=True),
    ] = False,
    generate_invoice: Annotated[
        Optional[bool],
        typer.Option("--invoice", "-i", help=docs["invoice"], show_default=False),
    ] = False,
    clean: Annotated[
        Optional[bool],
        typer.Option("--cleanup", "-c", help=docs["clean"], show_default=False),
    ] = False,
    output: Annotated[
        Optional[str],
        typer.Option("--output", "-o", help=docs["output"], show_default=False),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["export"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[str, typer.Argument(hidden=True)] = None,
) -> None:
    """*Beta:* Generate billable teams data."""

    from src.configuration import CLEANUP_AFTER
    from cli._export import Export
    from cli._format import Highlight
    from src.validators import (
        Validate,
        HostIdentityValidator,
        PermissionValidator,
    )

    validate = Validate(HostIdentityValidator(), PermissionValidator("sysadmin"))
    validate()

    output, export_dest, export_file_ext = _CLIExport(output, _export_dest)
    format = _CLIFormat(output, export_file_ext)

    from apps.bill_teams import UsersInformation, TeamsInformation, BillTeams

    users = UsersInformation(is_async_client)
    teams = TeamsInformation()
    bill_teams_ = BillTeams(users.items(), teams.items())
    bill_teams_data = bill_teams_.items()
    formatted_bill_teams_data = format(bill_teams_data)

    if export:
        export = Export(
            export_dest,
            file_name_prefix=bill_teams.__name__,
            file_extension=format.name,
        )
        export(data=formatted_bill_teams_data)
        console.print(export.success_message)
    else:
        highlight = Highlight(output)
        console.print(highlight(formatted_bill_teams_data))

    if generate_invoice:
        from apps.invoice import InvoiceGenerator

        invoice = InvoiceGenerator(bill_teams_data)
        export = Export(
            _export_dest,
            file_name_prefix="invoice",
            file_extension="md",
        )
        export(data=invoice.generate())
        console.print(export.success_message)

    if clean or CLEANUP_AFTER:
        typer.echo()  # mainly for a newline!
        cleanup()


if __name__ == "__main__":
    app()
