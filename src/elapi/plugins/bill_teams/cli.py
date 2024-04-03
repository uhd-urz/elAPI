from typing import Annotated, Optional

import tenacity
import typer
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from ._doc import __PARAMETERS__doc__ as docs
from ...cli.doc import __PARAMETERS__doc__ as elapi_docs
from ...configuration import APP_NAME, DEFAULT_EXPORT_DATA_FORMAT
from ...loggers import Logger
from ...styles import stdin_console, stderr_console
from ...validators import RuntimeValidationError

app = typer.Typer(
    rich_markup_mode="markdown",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
    name="bill-teams",
    help="Manage bills incurred by teams.",
)

logger = Logger()


@app.command(name="teams-info")
@tenacity.retry(
    retry=retry_if_exception_type((InterruptedError, RuntimeValidationError)),
    stop=stop_after_attempt(6),  # including the very first attempt
    wait=wait_exponential(multiplier=60, min=5, max=4260),
    retry_error_callback=lambda _: ...,  # meant to suppress raising final exception once all attempts have been made
)
def get_teams(
    data_format: Annotated[
        Optional[str],
        typer.Option(
            "--format", "-F", help=elapi_docs["data_format"], show_default=False
        ),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + elapi_docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
) -> dict:
    """Get billable teams data."""

    from ...cli.helpers import CLIExport, CLIFormat
    from ..commons import Export
    from ...styles import Highlight
    from ...validators import (
        Validate,
        HostIdentityValidator,
        PermissionValidator,
    )

    with stderr_console.status("Validating...\n", refresh_per_second=15):
        validate = Validate(HostIdentityValidator(), PermissionValidator("sysadmin"))
        validate()
    if export is False:
        _export_dest = None
    data_format, export_dest, export_file_ext = CLIExport(data_format, _export_dest)
    format = CLIFormat(data_format, export_file_ext)

    import asyncio
    from .bill_teams import (
        UsersInformation,
        TeamsInformation,
        TeamsList,
    )

    users_info, teams_info = UsersInformation(), TeamsInformation()
    try:
        tl = TeamsList(asyncio.run(users_info.items()), teams_info.items())
    except (RuntimeError, InterruptedError) as e:
        # RuntimeError is raised when users_items() -> event_loop.stop() stops the loop before future is completed.
        # InterruptedError is raised when JSONDecodeError is triggered.
        logger.info(f"{APP_NAME} will try again.")
        raise InterruptedError from e
    formatted_teams = format(teams := tl.items())

    if export:
        export_teams = Export(
            export_dest,
            file_name_stub="teams_info",
            file_extension=format.convention,
            format_name=format.name,
        )
        export_teams(data=formatted_teams, verbose=True)
    else:
        highlight = Highlight(format.name)
        stdin_console.print(highlight(formatted_teams))
    return teams


@app.command(name="owners-info")
def get_owners(
    owners_data_path: Annotated[
        str,
        typer.Option("--owners-data-path", help="", show_default=False),
    ],
    skip_essential_validation: Annotated[
        Optional[bool], typer.Option(hidden=True)
    ] = False,
    data_format: Annotated[
        Optional[str],
        typer.Option(
            "--format", "-F", help=elapi_docs["data_format"], show_default=False
        ),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + elapi_docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
) -> dict:
    """Get billable team owners data."""

    from ...cli.helpers import CLIExport, CLIFormat
    from ..commons import Export
    from ...styles import Highlight
    from ...validators import (
        Validate,
        HostIdentityValidator,
        PermissionValidator,
        Exit,
    )

    if not skip_essential_validation:
        with stderr_console.status("Validating...\n", refresh_per_second=15):
            validate = Validate(
                HostIdentityValidator(), PermissionValidator("sysadmin")
            )
            validate()
    if export is False:
        _export_dest = None
    data_format, export_dest, export_file_ext = CLIExport(data_format, _export_dest)
    format = CLIFormat(data_format, export_file_ext)

    from .bill_teams import (
        OwnersInformation,
        OwnersList,
    )

    owners_info = OwnersInformation(owners_data_path)
    try:
        ol = OwnersList(owners_info.items())
    except ValueError as e:
        logger.error(e)
        raise Exit(1)
    formatted_owners = format(owners := ol.items())

    if export:
        export_teams = Export(
            export_dest,
            file_name_stub="owners_info",
            file_extension=format.convention,
            format_name=format.name,
        )
        export_teams(data=formatted_owners, verbose=True)
    else:
        highlight = Highlight(format.name)
        stdin_console.print(highlight(formatted_owners))
    return owners


@app.command("generate-invoice")
def generate_invoice(
    _bill_teams_data: Annotated[
        Optional[str], typer.Option(hidden=True, show_default=False)
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["invoice_export"] + elapi_docs["export_details"],
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
    from ...cli.helpers import CLIExport
    from ...plugins.commons import Export
    from .invoice import InvoiceGenerator

    _INVOICE_FORMAT = "md"
    if export is False:
        _export_dest = None
    export = True  # export is always true for generate-invoice

    data_format, export_dest, _ = CLIExport(_INVOICE_FORMAT, _export_dest)
    if _bill_teams_data is None:
        _bill_teams_data = get_teams(
            data_format=DEFAULT_EXPORT_DATA_FORMAT, export=export
        )
    invoice = InvoiceGenerator(_bill_teams_data)
    export = Export(
        export_dest,
        file_name_stub="invoice",
        file_extension=data_format,
        format_name=_INVOICE_FORMAT,
    )
    export(data=invoice.generate(), verbose=True)
