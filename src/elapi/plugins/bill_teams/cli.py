from importlib.util import find_spec

import typer

PLUGIN_NAME: str = "bill-teams"

if not (find_spec("tenacity") and find_spec("dateutil")):
    ...
else:
    from typing import Annotated, Optional

    import tenacity
    from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

    from ._doc import __PARAMETERS__doc__ as docs
    from ...cli.doc import __PARAMETERS__doc__ as elapi_docs
    from ...configuration import APP_NAME, DEFAULT_EXPORT_DATA_FORMAT
    from ...loggers import Logger
    from ...styles import stdin_console, stderr_console
    from ...core_validators import RuntimeValidationError, Exit, ValidationError
    from ..commons.cli_helpers import Typer

    app = Typer(
        name=PLUGIN_NAME,
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
                "--format", "-F", help=docs["data_format"], show_default=False
            ),
        ] = None,
        sort_json_format: Annotated[bool, typer.Option(hidden=True)] = False,
        export: Annotated[
            Optional[bool],
            typer.Option(
                "--export",
                "-e",
                help=elapi_docs["export"] + docs["export_details"],
                is_flag=True,
                is_eager=True,
                show_default=False,
            ),
        ] = False,
        _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
        export_overwrite: Annotated[
            bool,
            typer.Option(
                "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
            ),
        ] = False,
    ) -> dict:
        """Get billable teams data."""
        from .format import remove_csv_formatter_support
        from ...plugins.commons.cli_helpers import CLIExport, CLIFormat
        from ..commons import Export
        from ...styles import Highlight
        from ...core_validators import Validate
        from ...api.validators import HostIdentityValidator, PermissionValidator
        from .specification import BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB

        remove_csv_formatter_support()

        with stderr_console.status("Validating...\n", refresh_per_second=15):
            validate = Validate(
                HostIdentityValidator(), PermissionValidator("sysadmin")
            )
            validate()
        if export is False:
            _export_dest = None

        if sort_json_format:
            from .format import JSONSortedFormat  # noqa: F401

        data_format, export_dest, export_file_ext = CLIExport(
            data_format, _export_dest, export_overwrite
        )
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
                file_name_stub=BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB,
                file_extension=format.convention,
                format_name=format.name,
            )
            export_teams(data=formatted_teams, verbose=True)
        else:
            highlight = Highlight(format.name)
            stdin_console.print(highlight(formatted_teams))
        return teams

    # noinspection PyUnresolvedReferences
    @app.command(name="owners-info")
    def get_owners(
        owners_data_path: Annotated[
            str,
            typer.Option(
                "--meta-source", help=docs["owners_data_path"], show_default=False
            ),
        ],
        skip_essential_validation: Annotated[bool, typer.Option(hidden=True)] = False,
        sort_json_format: Annotated[bool, typer.Option(hidden=True)] = False,
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
                help=elapi_docs["export"] + docs["export_details"],
                is_flag=True,
                is_eager=True,
                show_default=False,
            ),
        ] = False,
        _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
        export_overwrite: Annotated[
            bool,
            typer.Option(
                "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
            ),
        ] = False,
    ) -> dict:
        """Get billable team owners data."""
        from .format import remove_csv_formatter_support
        from ...plugins.commons.cli_helpers import CLIExport, CLIFormat
        from ..commons import Export
        from ...styles import Highlight
        from ...core_validators import (
            Validate,
            Exit,
            ValidationError,
        )
        from ...api.validators import HostIdentityValidator, PermissionValidator
        from .specification import BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB

        remove_csv_formatter_support()

        if not skip_essential_validation:
            with stderr_console.status("Validating...\n", refresh_per_second=15):
                validate = Validate(
                    HostIdentityValidator(), PermissionValidator("sysadmin")
                )
                validate()
        if export is False:
            _export_dest = None

        if sort_json_format:
            from .format import JSONSortedFormat  # noqa: F401

        data_format, export_dest, export_file_ext = CLIExport(
            data_format, _export_dest, export_overwrite
        )
        format = CLIFormat(data_format, export_file_ext)

        from .bill_teams import (
            TeamsInformation,
            OwnersInformation,
            OwnersList,
        )
        from .validator import OwnersInformationValidator

        teams_info, owners_info = (
            TeamsInformation(),
            OwnersInformation(owners_data_path),
        )
        try:
            validate_owners = Validate(
                OwnersInformationValidator(owners_info.items(), teams_info.items())
            )
            owners_validated = validate_owners.get()
        except ValidationError as e:
            logger.error(e)
            logger.error("Owners data could not be validated!")
            raise Exit(1)
        try:
            ol = OwnersList(owners_validated)
        except ValueError as e:
            logger.error(e)
            raise Exit(1)
        formatted_owners = format(owners := ol.items())

        if export:
            export_teams = Export(
                export_dest,
                file_name_stub=BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB,
                file_extension=format.convention,
                format_name=format.name,
            )
            export_teams(data=formatted_owners, verbose=True)
        else:
            highlight = Highlight(format.name)
            stdin_console.print(highlight(formatted_owners))
        return owners

    @app.command("generate-invoice", deprecated=True, hidden=True)
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
        from rich.live import Live
        from os import devnull
        import contextlib
        from ...plugins.commons.cli_helpers import CLIExport
        from ...plugins.commons import Export
        from .invoice import InvoiceGenerator

        _INVOICE_FORMAT = "md"
        if export is False:
            _export_dest = None
        logger.warning(
            "Due to deprecation, the generated invoice will not reflect accurate information. "
            "Some behaviors have been removed."
        )
        data_format, export_dest, _ = CLIExport(_INVOICE_FORMAT, _export_dest)
        with Live("Generating invoice..."):
            ...
        with open(devnull, "w") as devnull:
            with contextlib.redirect_stdout(devnull):
                if _bill_teams_data is None:
                    _bill_teams_data = get_teams(data_format=DEFAULT_EXPORT_DATA_FORMAT)
        invoice = InvoiceGenerator(_bill_teams_data)
        export = Export(  # export is always true for generate-invoice
            export_dest,
            file_name_stub="invoice",
            file_extension=data_format,
            format_name=_INVOICE_FORMAT,
        )
        export(data=invoice.generate(), verbose=True)

    # noinspection PyTypeChecker
    @app.command(name="store-info")
    def store_teams_and_owners(
        root_directory: Annotated[
            str,
            typer.Option("--root-dir", help=docs["root_directory"], show_default=False),
        ],
        owners_data_path: Annotated[
            str,
            typer.Option(
                "--meta-source", help=docs["owners_data_path"], show_default=False
            ),
        ] = None,
        target_date: Annotated[
            Optional[str],
            typer.Option("--target-date", help=docs["target_date"], show_default=False),
        ] = None,
        teams_info_only: Annotated[
            Optional[bool],
            typer.Option(
                "--teams-info-only", help=docs["teams_info_only"], show_default=False
            ),
        ] = None,
        owners_info_only: Annotated[
            Optional[bool],
            typer.Option(
                "--owners-info-only", help=docs["owners_info_only"], show_default=False
            ),
        ] = None,
    ) -> None:
        """
        Store billable teams and team owners data.

        `store-info` essentially runs `teams-info` and `owners-info` but takes over their export location, and
        instead stores the output information in a pre-defined directory structure.

        **Example**:

        `$ elapi bill-teams store-info --root-dir ~/bill-teams --meta-source <CSV file path to owners information>` will
        store the information in the following structure. _YYYY_ and _MM_ refer to year and month number respectively.

        ```sh
        ~/bill-teams/
        └── YYYY/
            └── MM/
                ├── <YYYY-MM-DD_HHMMSS>_owners_info.json
                └── <YYYY-MM-DD_HHMMSS>_teams_info.json
        ```
        """
        from ...styles import print_typer_error
        from ...path import ProperPath
        from ...core_validators import Validate, PathValidator, ValidationError
        from .specification import (
            CLI_DATE_VALID_FORMAT,
            CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN,
        )
        from datetime import datetime
        from dateutil import parser
        import re

        if teams_info_only is True and owners_info_only is True:
            print_typer_error(
                "Both '--team-info-only' and '--owners-info-only' cannot be passed "
                "as the meaning is ambiguous!"
            )
            raise Exit(1)

        if not ProperPath(root_directory).kind == "dir":
            print_typer_error("'--root-dir' must be a path to a directory.")
            raise Exit(1)
        try:
            validate_path = Validate(PathValidator(root_directory))
            root_directory: ProperPath = validate_path.get()
        except ValidationError:
            logger.error(
                f"--root-dir path '{root_directory}' could not be validated! Data could not be stored in desired location."
            )
            raise Exit(1)
        if target_date is None:
            target_date = datetime.now()
        else:
            try:
                target_date = parser.isoparse(user_target_date := target_date.strip())
            except ValueError as e:
                print_typer_error(
                    f"'--target-date' is given an invalid ISO 8601 date '{target_date}'."
                )
                raise Exit(1) from e
            else:
                if not re.match(
                    rf"{CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN}", user_target_date
                ):
                    print_typer_error(
                        f"'--target-date' is valid ISO 8601, but it must also be "
                        f"in '{CLI_DATE_VALID_FORMAT}' format."
                    )
                    raise Exit(1)
        target_year = str(target_date.year)
        target_month = f"{target_date.month:02d}"
        store_location = root_directory / target_year / target_month

        if teams_info_only is True:
            get_teams(sort_json_format=True, export=True, _export_dest=store_location)
            return
        if owners_info_only is True:
            if owners_data_path is None:
                print_typer_error(
                    "When '--owners-info-only' is passed '--meta-source' must be provided as well!"
                )
                raise Exit(1)
            get_owners(
                owners_data_path,
                sort_json_format=True,
                export=True,
                _export_dest=store_location,
            )
            return
        if owners_data_path is None:
            print_typer_error("Missing option '--meta-source'.")
            raise Exit(1)
        get_teams(sort_json_format=True, export=True, _export_dest=store_location)
        get_owners(
            owners_data_path,
            skip_essential_validation=True,
            sort_json_format=True,
            export=True,
            _export_dest=store_location,
        )

    @app.command(name="generate-table")
    def generate_table(
        root_directory: Annotated[
            str,
            typer.Option("--root-dir", help=docs["root_directory"], show_default=False),
        ],
        user_start_date: Annotated[
            Optional[str],
            typer.Option("--start-date", help="", show_default=False),
        ] = None,
        user_end_date: Annotated[
            Optional[str],
            typer.Option("--end-date", help="", show_default=False),
        ] = None,
    ) -> None:
        """
        Generate final table for billing, a.k.a. "output table".
        """
        import re
        from dateutil import parser
        from dateutil.relativedelta import relativedelta
        from ...styles import print_typer_error
        from ...path import ProperPath
        from ...core_validators import Validate
        from .validators import BillingInformationPathValidator
        from .generate_table import get_billing_dates
        from .specification import (
            BILLING_BASE_DATE,
            BILLING_PERIOD,
            CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN,
            CLI_DATE_VALID_FORMAT,
        )

        if not ProperPath(root_directory).kind == "dir":
            print_typer_error("'--root-dir' must be a path to a directory.")
            raise Exit(1)
        base_date = BILLING_BASE_DATE

        def parse_user_input_date(user_date: str, /, date_cli_arg: str):
            if not isinstance(user_date, str):
                raise ValueError("user_date must be a string.")
            try:
                date = parser.isoparse(user_date.strip())
            except ValueError as error:
                print_typer_error(
                    f"'{date_cli_arg}' is given an invalid ISO 8601 date '{user_date}'."
                )
                raise Exit(1) from error
            else:
                if not re.match(rf"{CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN}", user_date):
                    print_typer_error(
                        f"{date_cli_arg} '{user_date}' is valid ISO 8601, but it must "
                        f"also be in '{CLI_DATE_VALID_FORMAT}' format."
                    )
                    raise Exit(1)
                return date

        if not isinstance(user_start_date, (str, type(None))):
            raise ValueError(
                "'--start-date' received a value of unsupported type. "
                f"Calling method isn't meant to be evoked from outside the CLI."
                f"{APP_NAME} plugin {PLUGIN_NAME} will abort."
            )
        if not isinstance(user_end_date, (str, type(None))):
            raise ValueError(
                "'--end-date' received a value of unsupported type. "
                "Calling method isn't meant to be evoked from outside the CLI. "
                f"{APP_NAME} plugin {PLUGIN_NAME} will abort."
            )
        # The default values of start_date and end_date. I.e., if user_start_date is None and user_end_date is None.
        start_date = base_date - relativedelta(months=BILLING_PERIOD)
        end_date = base_date
        if user_start_date is None and user_end_date is not None:
            end_date = parse_user_input_date(user_end_date, "--end-date")
            start_date = end_date - relativedelta(months=BILLING_PERIOD)
        elif user_start_date is not None and user_end_date is None:
            start_date = parse_user_input_date(user_start_date, "--start-date")
            end_date = start_date + relativedelta(months=BILLING_PERIOD)
        elif user_start_date is not None and user_end_date is not None:
            start_date = parse_user_input_date(user_start_date, "--start-date")
            end_date = parse_user_input_date(user_end_date, "--end-date")
            if end_date < start_date:
                print_typer_error(
                    f"--start-date '{user_start_date}' cannot be be ahead of "
                    f"--end-date '{user_end_date}'!"
                )
                raise Exit(1)

        valid_paths: list[ProperPath] = []
        for year, month in get_billing_dates(start_date, end_date):
            try:
                path = Validate(
                    BillingInformationPathValidator(
                        root_directory, year, month, err_logger=logger
                    )
                ).get()
            except ValidationError as e:
                logger.error(e)
                raise Exit(1)
            else:
                valid_paths.append(path)
