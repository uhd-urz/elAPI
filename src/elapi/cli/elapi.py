#!/usr/bin/python3

"""``elAPI`` is a powerful, extensible API interface to eLabFTW. It supports serving almost all kinds of requests
documented in https://doc.elabftw.net/api/v2/ with ease. elAPI treats eLabFTW API endpoints as its arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elAPI you can do the following:
        $ elapi get users --id <id>
"""
from typing import Optional

import tenacity
import typer
from rich import pretty
from rich.console import Console
from rich.markdown import Markdown
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential
from typing_extensions import Annotated

from ._doc import __PARAMETERS__doc__ as docs
from ..configuration import APP_NAME
from ..loggers import Logger
from ..path import ProperPath
from ..styles import get_custom_help_text
from ..validators import RuntimeValidationError

logger = Logger()


pretty.install()
console = Console(color_system="truecolor")
app = typer.Typer(rich_markup_mode="markdown", pretty_exceptions_show_locals=False)
bill_teams_app = typer.Typer(
    rich_markup_mode="markdown", pretty_exceptions_show_locals=False
)
app.add_typer(bill_teams_app, name="bill-teams", help="Manage bills incurred by teams.")

typer.rich_utils.STYLE_HELPTEXT = (
    ""  # fixes https://github.com/tiangolo/typer/issues/437
)
typer.rich_utils._get_help_text = (
    get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447
)


class _CLIExport:
    def __new__(
        cls, data_format: Optional[str] = None, export_dest: Optional[str] = None
    ):
        from collections import namedtuple
        from ..validators import Validate
        from ..plugins.export import ExportValidator

        validate_export = Validate(ExportValidator(export_dest))
        export_dest: ProperPath = validate_export.get()

        _export_file_ext: str = (
            export_dest.expanded.suffix.removeprefix(".")
            if export_dest.kind == "file"
            else None
        )
        data_format = (
            data_format or _export_file_ext or "json"
        )  # default data_format format
        ExportParams = namedtuple(
            "ExportParams", ["data_format", "destination", "extension"]
        )
        return ExportParams(data_format, export_dest, _export_file_ext)


class _CLIFormat:
    def __new__(cls, data_format: str, export_file_ext: Optional[str] = None):
        from ..styles import Format

        try:
            format = Format(data_format)
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
    data_format: Annotated[
        Optional[str],
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
) -> dict:
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
    `$ elapi get users` will return list of all users.
    <br/>
    `$ elapi get users --id <id>` will return information about the specific user `<id>`.
    """
    from ..api import GETRequest
    from ..validators import Validate, HostIdentityValidator
    from ..plugins.export import Export
    from ..styles import Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if export is False:
        _export_dest = None

    data_format, export_dest, export_file_ext = _CLIExport(data_format, _export_dest)
    format = _CLIFormat(data_format, export_file_ext)

    session = GETRequest()
    raw_response = session(endpoint, unit_id)

    formatted_data = format(response_data := raw_response.json())

    if export:
        file_name_stub = f"{endpoint}_{unit_id}" if unit_id else f"{endpoint}"
        export = Export(
            export_dest,
            file_name_stub=file_name_stub,
            file_extension=format.name,
        )
        export(data=formatted_data, verbose=True)
    else:
        highlight = Highlight(data_format)
        console.print(highlight(formatted_data))
    return response_data


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
    ],
    # data: typer.Context = None,  TODO: To be re-enabled in Python 3.11
    data_format: Annotated[
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
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
    `$ elapi post users -d '{"firstname": "John", "lastname": "Doe", "email": "test_test@itnerd.de"}'` will create a new user.
    """
    import ast
    from ..api import POSTRequest
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..styles import Format, Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    # if json_:
    valid_data: dict = ast.literal_eval(json_)
    # else:
    # TODO: Due to strange compatibility issue between typer.context and python 3.9,
    #   passing json_ as arguments is temporarily deprecated.
    # data_keys: list[str, ...] = [_.removeprefix("--") for _ in data.args[::2]]
    # data_values: list[str, ...] = data.args[1::2]
    # valid_data: dict[str:str, ...] = dict(zip(data_keys, data_values))
    session = POSTRequest()
    raw_response = session(endpoint, unit_id, **valid_data)
    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            console.print("Success: Resource created!", style="green")
        else:
            console.print(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'.",
                style="red",
            )
    else:
        highlight = Highlight(data_format)
        console.print(highlight(formatted_data))


@app.command(name="show-config")
def show_config(
    show_keys: Annotated[
        Optional[bool],
        typer.Option("--show-keys", "-k", help=docs["show_keys"], show_default=True),
    ] = False,
) -> None:
    """
    Get information about detected configuration values.
    """
    from ..plugins.show_config import show

    md = Markdown(show(show_keys))
    console.print(md)


@app.command(
    hidden=True, deprecated=True
)  # deprecated instead of removing for future use
def cleanup() -> None:
    """
    Remove cached data.
    """
    from ..configuration import TMP_DIR
    from ..path import ProperPath
    from time import sleep

    with console.status("Cleaning up...", refresh_per_second=15):
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        ProperPath(TMP_DIR, err_logger=logger).remove(verbose=True)
    console.print("Done!", style="green")


@bill_teams_app.command(name="info")
@tenacity.retry(
    retry=retry_if_exception_type((InterruptedError, RuntimeValidationError)),
    stop=stop_after_attempt(6),  # including the very first attempt
    wait=wait_exponential(multiplier=60, min=5, max=4260),
    retry_error_callback=lambda _: ...,  # meant to suppress raising final exception once all attempts have been made
)
def bill_teams(
    data_format: Annotated[
        Optional[str],
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
) -> dict:
    """Get billable teams data."""

    from ..plugins.export import Export
    from ..styles import Highlight
    from ..validators import (
        Validate,
        HostIdentityValidator,
        PermissionValidator,
    )

    with console.status("Validating...\n", refresh_per_second=15):
        validate = Validate(HostIdentityValidator(), PermissionValidator("sysadmin"))
        validate()
    if export is False:
        _export_dest = None
    data_format, export_dest, export_file_ext = _CLIExport(data_format, _export_dest)
    format = _CLIFormat(data_format, export_file_ext)

    import asyncio
    from ..plugins.bill_teams import (
        UsersInformation,
        TeamsInformation,
        BillTeams,
    )

    users, teams = UsersInformation(), TeamsInformation()
    try:
        bill = BillTeams(asyncio.run(users.items()), teams.items())
    except RuntimeError as e:
        # RuntimeError is raised when users_items() -> event_loop.stop() stops the loop before all tasks are finished
        logger.info(f"{APP_NAME} will try again.")
        raise InterruptedError from e
    bill_teams_data = bill.items()
    formatted_bill_teams_data = format(bill_teams_data)

    if export:
        export = Export(
            export_dest,
            file_name_stub=bill_teams.__name__,
            file_extension=format.name,
        )
        export(data=formatted_bill_teams_data, verbose=True)
    else:
        highlight = Highlight(data_format)
        console.print(highlight(formatted_bill_teams_data))
    return bill_teams_data


@bill_teams_app.command("generate-invoice")
def generate_invoice(
    _bill_teams_data: Annotated[
        Optional[str], typer.Option(hidden=True, show_default=False)
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["invoice_export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
):
    """
    Generate invoice for billable teams.
    """
    from ..plugins.export import Export
    from ..plugins.bill_teams import InvoiceGenerator

    if export is False:
        _export_dest = None
    export = True  # export is always true for generate-invoice

    data_format, export_dest, _ = _CLIExport("md", _export_dest)
    if _bill_teams_data is None:
        _bill_teams_data = bill_teams(data_format="yaml", export=export)
    invoice = InvoiceGenerator(_bill_teams_data)
    export = Export(
        export_dest,
        file_name_stub="invoice",
        file_extension=data_format,
    )
    export(data=invoice.generate(), verbose=True)
