import json
from datetime import datetime
from functools import partial
from importlib.util import find_spec
from pathlib import Path

import typer

from .generate_table import is_team_on_trial
from .names import PLUGIN_NAME, REGISTRY_SUB_PLUGIN_NAME, TARGET_GROUP_NAME

if not (find_spec("tenacity") and find_spec("dateutil") and find_spec("uvloop")):
    ...
else:
    import re
    import uvloop
    from typing import Annotated, Optional, Tuple, Generator, Union

    import tenacity
    from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

    from dateutil.relativedelta import relativedelta
    from dateutil import parser
    from ...styles import print_typer_error
    from ._doc import __PARAMETERS__doc__ as docs
    from ...cli.doc import __PARAMETERS__doc__ as elapi_docs
    from ...configuration import APP_NAME, get_active_export_dir
    from ...loggers import Logger
    from ...styles import stdout_console, stderr_console
    from ...core_validators import RuntimeValidationError, Exit, ValidationError
    from ..commons.cli_helpers import Typer
    from ...styles import __PACKAGE_IDENTIFIER__ as styles_package_identifier
    from .configuration import get_root_dir
    from .utils import get_billing_dates
    from ..commons import Export
    from ...styles import Highlight
    from ...plugins.commons.cli_helpers import CLIExport, CLIFormat
    from ...utils.typer_patches import patch_typer_flag_value
    from .registry import (
        _initialize_registry_file,
        _is_team_bill_generation_metadata_sane,
        _update_registry_team_bill_generation_metadata,
        modify_registry_file,
        registry_spec,
        _registry_communication,
    )
    from .specification import (
        BILLING_BASE_DATE,
        BILLING_PERIOD,
        CLI_DATE_PARSE_SIMPLE_REGEX_PATTERN,
        CLI_DATE_VALID_FORMAT,
        REGISTRY_FILE_NAME,
        BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB,
        BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB,
        _registry_com_spec,
        owners_spec,
        ot_header_spec,
        ot_header_billing_period_spec,
        get_billing_period_header_entry,
        ot_fixed_texts_spec,
        de_months,
        OUTPUT_TABLE_NAN_INDICATOR as NAN,
        METADATA_BILLING_INTERNAL_EXTERNAL_TO_BOOL as int_ext_to_bool,
        OUTPUT_TABLE_FILE_NAME_STUB,
    )

    patch_typer_flag_value()
    app = Typer(
        name=PLUGIN_NAME,
        help="Manage bills incurred by teams.",
    )

    registry_app = Typer(
        name=REGISTRY_SUB_PLUGIN_NAME, help=f"Manage {PLUGIN_NAME} registry."
    )
    app.add_typer(registry_app, rich_help_panel=f"Sub-plugins")

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
        highlight_syntax: Annotated[
            Optional[bool],
            typer.Option(
                "--highlight",
                "-H",
                help=elapi_docs["highlight_syntax"],
                show_default=True,
            ),
        ] = False,
        sort_json_format: Annotated[bool, typer.Option(hidden=True)] = False,
        export: Annotated[
            Optional[str],
            typer.Option(
                "--export",
                "-e",
                help=elapi_docs["export"] + docs["export_details"],
                is_flag=False,
                flag_value="",
                show_default=False,
            ),
        ] = None,
        export_overwrite: Annotated[
            bool,
            typer.Option(
                "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
            ),
        ] = False,
    ) -> dict:
        """Get billable teams data."""
        from ...api import GlobalSharedSession
        from ...core_validators import Validate
        from ...api.validators import HostIdentityValidator, PermissionValidator

        global_session = GlobalSharedSession()
        with stderr_console.status(
            "Validating...\n", refresh_per_second=15
        ) as validation_status:
            validate = Validate(
                HostIdentityValidator(), PermissionValidator("sysadmin")
            )
            try:
                validate()
            except RuntimeValidationError as e:
                validation_status.stop()
                raise e
        if export == "":
            export = get_active_export_dir()
        if sort_json_format is True:
            package_identifier: str = __package__
        else:
            package_identifier: str = styles_package_identifier
        data_format, export_dest, export_file_ext = CLIExport(
            data_format, export, export_overwrite
        )
        format = CLIFormat(data_format, package_identifier, export_file_ext)

        from .bill_teams import (
            UsersInformation,
            TeamsInformation,
            TeamsList,
        )

        users_info, teams_info = UsersInformation(), TeamsInformation()

        async def gather_teams_list() -> TeamsList:
            try:
                tl = TeamsList(await users_info.items(), teams_info.items())
            except (RuntimeError, InterruptedError) as error:
                global_session.close()
                logger.info(f"{APP_NAME} will try again.")
                raise InterruptedError from error
            else:
                global_session.close()
            return tl

        teams_list = uvloop.run(gather_teams_list())
        formatted_teams = format(teams := teams_list.items())
        if export is not None:
            export_teams = Export(
                export_dest,
                file_name_stub=BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB,
                file_extension=format.convention,
                format_name=format.name,
            )
            export_teams(data=formatted_teams, verbose=True)
        else:
            if highlight_syntax is True:
                highlight = Highlight(format.name, package_identifier=__package__)
                stdout_console.print(highlight(formatted_teams))
            else:
                typer.echo(formatted_teams)
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
        highlight_syntax: Annotated[
            Optional[bool],
            typer.Option(
                "--highlight",
                "-H",
                help=elapi_docs["highlight_syntax"],
                show_default=True,
            ),
        ] = False,
        export: Annotated[
            Optional[str],
            typer.Option(
                "--export",
                "-e",
                help=elapi_docs["export"] + docs["export_details"],
                is_flag=False,
                flag_value="",
                show_default=False,
            ),
        ] = None,
        export_overwrite: Annotated[
            bool,
            typer.Option(
                "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
            ),
        ] = False,
    ) -> dict:
        """Get billable team owners data."""
        from ...core_validators import (
            Validate,
            Exit,
            ValidationError,
        )
        from ...api import GlobalSharedSession
        from ...api.validators import HostIdentityValidator, PermissionValidator

        if not skip_essential_validation:
            with GlobalSharedSession(limited_to="sync"):
                with stderr_console.status(
                    "Validating...\n", refresh_per_second=15
                ) as validation_status:
                    validate = Validate(
                        HostIdentityValidator(), PermissionValidator("sysadmin")
                    )
                    try:
                        validate()
                    except RuntimeValidationError as e:
                        validation_status.stop()
                        raise e
        if export == "":
            export = get_active_export_dir()

        if sort_json_format is True:
            package_identifier: str = __package__
        else:
            package_identifier: str = styles_package_identifier

        data_format, export_dest, export_file_ext = CLIExport(
            data_format, export, export_overwrite
        )
        format = CLIFormat(data_format, package_identifier, export_file_ext)

        from .bill_teams import (
            TeamsInformation,
            OwnersInformation,
            OwnersList,
        )
        from .validators import OwnersInformationValidator

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

        if export is not None:
            export_teams = Export(
                export_dest,
                file_name_stub=BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB,
                file_extension=format.convention,
                format_name=format.name,
            )
            export_teams(data=formatted_owners, verbose=True)
        else:
            if highlight_syntax is True:
                highlight = Highlight(format.name, package_identifier=__package__)
                stdout_console.print(highlight(formatted_owners))
            else:
                typer.echo(formatted_owners)
        return owners

    # noinspection PyTypeChecker
    @app.command(name="store-info")
    def store_teams_and_owners(
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

        `$ elapi bill-teams store-info --meta-source <CSV file path to owners information>` will
        store the information in the following structure.
        The export location `root_dir: <directory>` must be defined under
        `plugins.bill_teams` in the configuration file. _YYYY_ and _MM_ refer to year and month number respectively.

        ```sh
        ~/bill-teams/  # from root_dir: ~/bill-teams/ in elapi.yml
        └── YYYY/
            └── MM/
                ├── <YYYY-MM-DD_HHMMSS>_owners_info.json
                └── <YYYY-MM-DD_HHMMSS>_teams_info.json
        ```
        """
        from ...styles import print_typer_error
        from ...path import ProperPath
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

        root_directory: ProperPath = ProperPath(get_root_dir())
        root_directory.create()
        # Not strictly necessary, as Export already crates the paren directories,
        # but mainly for the log.
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
            get_teams(sort_json_format=True, export=str(store_location))
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
                export=str(store_location),
            )
            return
        if owners_data_path is None:
            print_typer_error("Missing option '--meta-source'.")
            raise Exit(1)
        _teams_info = get_teams(sort_json_format=True, export=str(store_location))
        get_owners(
            owners_data_path,
            skip_essential_validation=True,
            sort_json_format=True,
            export=str(store_location),
        )

    def _parse_cli_input_date(user_date: str, /, date_cli_arg: str):
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

    def _parse_user_billing_dates(
        user_start_date: Optional[str] = None, user_end_date: Optional[str] = None
    ) -> Tuple[datetime, datetime]:
        base_date = BILLING_BASE_DATE

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
        # The initial values of start_date and end_date
        start_date = base_date - relativedelta(months=BILLING_PERIOD)
        end_date = base_date
        if user_start_date is None and user_end_date is None:
            end_date = end_date - relativedelta(months=1)
            start_date = end_date - relativedelta(months=BILLING_PERIOD)
        elif user_start_date is None and user_end_date is not None:
            end_date = _parse_cli_input_date(user_end_date, "--end-date")
            start_date = end_date - relativedelta(months=BILLING_PERIOD)
        elif user_start_date is not None and user_end_date is None:
            start_date = _parse_cli_input_date(user_start_date, "--start-date")
            end_date = start_date + relativedelta(months=BILLING_PERIOD)
        elif user_start_date is not None and user_end_date is not None:
            start_date = _parse_cli_input_date(user_start_date, "--start-date")
            end_date = _parse_cli_input_date(user_end_date, "--end-date")
            if end_date < start_date:
                print_typer_error(
                    f"--start-date '{user_start_date}' cannot be be ahead of "
                    f"--end-date '{user_end_date}'!"
                )
                raise Exit(1)
        return start_date, end_date

    def _get_dates(
        user_start_date: Optional[str], user_end_date: Optional[str] = None
    ) -> list[Tuple[int, int]]:
        registry_dates: list[Tuple[int, int]] = []
        for year, month in get_billing_dates(
            *_parse_user_billing_dates(user_start_date, user_end_date)
        ):
            registry_dates.append((year, month))
        return registry_dates

    def _get_registry(
        billing_dates: list[Tuple[int, int]],
    ) -> Generator[Tuple[Path, dict], None, None]:
        from ...path import ProperPath
        from ...core_validators import Validate
        from .validators import (
            BillingInformationPathValidator,
            BillingRegistryValidator,
        )

        for year, month in billing_dates:
            try:
                billing_info = Validate(
                    BillingInformationPathValidator(
                        get_root_dir(), year, month, err_logger=logger
                    )
                ).get()
            except ValidationError as e:
                logger.error(e)
                raise Exit(1) from e
            else:
                info_parent_dir, teams_info_file_metadata, owners_info_file_metadata = (
                    billing_info
                )
                registry_file_path = info_parent_dir / REGISTRY_FILE_NAME
                _initialize_registry_file(
                    registry_file_path,
                    year,
                    month,
                    teams_info_file_metadata,
                    owners_info_file_metadata,
                )
                try:
                    registry_data = Validate(
                        BillingRegistryValidator(
                            registry_file_path,
                            teams_info_file_metadata,
                            owners_info_file_metadata,
                        )
                    ).get()
                except ValidationError as e:
                    logger.error(e)
                    raise Exit(1) from e
                else:
                    yield registry_file_path, registry_data

    def _user_warn_team_is_missing_in_teams_info():
        from ...loggers import SimpleLogger
        from ..._names import LOG_FILE_NAME

        stdout_logger = SimpleLogger()
        if (
            _registry_communication[
                _registry_com_spec.EXISTS_IN_OWNERS_INFO_BUT_MISSING_IN_TEAMS_INFO
            ]
            is True
        ):
            stdout_logger.warning(
                f"One or more teams exist in '{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}', "
                f"but are missing in '{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}'. "
                f"See {LOG_FILE_NAME} file for more information."
            )

    @registry_app.command(name="include")
    def include(
        team_id: Annotated[
            Optional[str],
            typer.Option(
                "--team-id", help=docs["registry_team_id"], show_default=False
            ),
        ] = "all",
        user_start_date: Annotated[
            Optional[str],
            typer.Option("--start-date", help=docs["start_date"], show_default=False),
        ] = None,
        user_end_date: Annotated[
            Optional[str],
            typer.Option("--end-date", help=docs["end_date"], show_default=False),
        ] = None,
        do_not_print_missing_in_teams_info: Annotated[
            Optional[bool],
            typer.Option(
                "--do-not-print-missing-in-teams-info-log",
                "--dnpm",
                help=docs["do_not_print_missing_in_teams_info_log"],
                show_default=True,
            ),
        ] = False,
        force: Annotated[
            Optional[bool],
            typer.Option(
                "--force",
                help=docs["include_force"],
                show_default=True,
            ),
        ] = False,
    ) -> None:
        """
        Include teams to output table.
        """
        _registry_communication[
            _registry_com_spec.USER_REQUESTED_FILE_LOG_FOR_MISSING_TEAMS_INFO
        ] = do_not_print_missing_in_teams_info
        registries = list(
            _get_registry((billing_dates := _get_dates(user_start_date, user_end_date)))
        )
        registry_billing_dates = ", ".join(
            f"{year}-{month:02d}" for year, month in billing_dates
        )
        is_sane: bool = True
        for registry_file_path, registry_data in registries:
            if (
                _is_team_bill_generation_metadata_sane(
                    registry_data,
                    registry_file_path=registry_file_path,
                    team_id=team_id,
                    ideal_include_status="include",
                )
                is False
            ):
                is_sane = False
        if do_not_print_missing_in_teams_info is True:
            _user_warn_team_is_missing_in_teams_info()
        if is_sane is True or force is True:
            for registry_file_path, registry_data in registries:
                _update_registry_team_bill_generation_metadata(
                    registry_data,
                    team_id=team_id,
                    include_status="include",
                    counter_status=None,
                )
                modify_registry_file(registry_file_path, registry_data)
            if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
                logger.info(
                    f"All teams have been included to registry "
                    f"for the following dates: {registry_billing_dates}. "
                    f"All teams will be considered for billing for those dates."
                )
            else:
                logger.info(
                    f"Team with team ID '{team_id}' has been included to registry "
                    f"for the following dates: {registry_billing_dates}. "
                    f"Team will be considered for billing for those dates."
                )
        else:
            if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
                logger.error(
                    f"Registry cannot be modified for all teams. "
                    f"Please pass '--force' to force include teams to registry."
                )
                raise Exit(1)
            logger.error(
                f"Registry cannot be modified for team '{team_id}'. "
                f"Please pass '--force' to force include team to registry."
            )
            raise Exit(1)

    @registry_app.command(name="exempt")
    def exempt(
        team_id: Annotated[
            Optional[str],
            typer.Option(
                "--team-id", help=docs["registry_team_id"], show_default=False
            ),
        ] = "all",
        user_start_date: Annotated[
            Optional[str],
            typer.Option("--start-date", help=docs["start_date"], show_default=False),
        ] = None,
        user_end_date: Annotated[
            Optional[str],
            typer.Option("--end-date", help=docs["end_date"], show_default=False),
        ] = None,
        do_not_print_missing_in_teams_info: Annotated[
            Optional[bool],
            typer.Option(
                "--do-not-print-missing-in-teams-info-log",
                "--dnpm",
                help=docs["do_not_print_missing_in_teams_info_log"],
                show_default=True,
            ),
        ] = False,
    ) -> None:
        """
        Exempt teams from billing (or going into output table).
        """
        from .registry import (
            _is_team_bill_generation_metadata_sane,
            _update_registry_team_bill_generation_metadata,
            modify_registry_file,
        )

        for registry_file_path, registry_data in _get_registry(
            (billing_dates := _get_dates(user_start_date, user_end_date))
        ):
            _update_registry_team_bill_generation_metadata(
                registry_data,
                team_id=team_id,
                include_status="exempt",
                counter_status=None,
            )
            modify_registry_file(registry_file_path, registry_data)
        if do_not_print_missing_in_teams_info is True:
            _user_warn_team_is_missing_in_teams_info()
        registry_billing_dates = ", ".join(
            f"{year}-{month:02d}" for year, month in billing_dates
        )
        if team_id == registry_spec.REGISTRY_CLI_IMPLICIT_ARG_INCLUDE_ALL_TEAMS:
            logger.info(
                "All teams have been exempted from registry "
                f"for the following dates: {registry_billing_dates}. "
                "All teams will not be considered for billing for those dates."
            )
        else:
            logger.info(
                f"Team with team ID '{team_id}' has been exempted from registry "
                f"for the following dates: {registry_billing_dates}. "
                f"Team will not be considered for billing for those dates."
            )

    @app.command(name="generate-table")
    def generate_table(
        user_start_date: Annotated[
            Optional[str],
            typer.Option("--start-date", help=docs["start_date"], show_default=False),
        ] = None,
        user_end_date: Annotated[
            Optional[str],
            typer.Option("--end-date", help=docs["end_date"], show_default=False),
        ] = None,
        datum: Annotated[
            Optional[str],
            typer.Option("--datum", help=docs["ot_datum"], show_default=False),
        ] = None,
        include_monthly_bill: Annotated[
            Optional[bool],
            typer.Option(
                "--include-monthly-bill",
                "--imb",
                help=docs["ot_include_monthly_bill"],
                show_default=True,
            ),
        ] = False,
        include_team_id: Annotated[
            Optional[bool],
            typer.Option(
                "--include-team-id",
                "--iti",
                help=docs["ot_include_team_id"],
                show_default=True,
            ),
        ] = False,
        dry_run: Annotated[
            Optional[bool],
            typer.Option(
                "--do-not-update-registry",
                "--dry-run",
                help=docs["ot_dry_run"],
                show_default=True,
            ),
        ] = False,
        ignore_exempt: Annotated[
            Optional[bool],
            typer.Option(
                "--ignore-exempt",
                help=docs["ot_ignore_exempt"],
                show_default=True,
            ),
        ] = False,
        data_format: Annotated[
            Optional[str],
            typer.Option(
                "--format", "-F", help=elapi_docs["data_format"], show_default=False
            ),
        ] = None,
        highlight_syntax: Annotated[
            Optional[bool],
            typer.Option(
                "--highlight",
                "-H",
                help=elapi_docs["highlight_syntax"],
                show_default=True,
            ),
        ] = False,
        export: Annotated[
            Optional[str],
            typer.Option(
                "--export",
                "-e",
                help=elapi_docs["export"] + docs["export_details"],
                is_flag=False,
                flag_value="",
                show_default=False,
            ),
        ] = None,
        export_overwrite: Annotated[
            bool,
            typer.Option(
                "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
            ),
        ] = False,
    ) -> None:
        """
        Generate final table for billing, a.k.a. "output table".
        """
        from .generate_table import (
            get_ot_template,
            can_ignore_team,
            can_exempt_team,
            _update_registry_single_team_bill_generation_metadata,
            calculate_team_monthly_bill,
            is_billing_management_limited,
            get_text_1,
            get_text_2,
        )

        if ignore_exempt is True:
            dry_run = True
        if export == "":
            export = get_active_export_dir()
        DE_MONTHS_ONLY = list(de_months.__dict__.values())
        if datum is None:
            datum = BILLING_BASE_DATE
        else:
            datum = _parse_cli_input_date(datum, "--datum")
        registry_files_info: list[Tuple[Path, int, int]] = []
        for year, month in get_billing_dates(
            *_parse_user_billing_dates(user_start_date, user_end_date)
        ):
            path = get_root_dir() / str(year) / f"{month:02d}" / REGISTRY_FILE_NAME
            if not path.exists():
                logger.error(
                    f"{REGISTRY_FILE_NAME} file in root directory with "
                    f"month '{month}' of year '{year}': '{path}' doesn't exist!"
                )
                raise Exit(1)
            registry_files_info.append((path, year, month))
        data_format, export_dest, export_file_ext = CLIExport(
            data_format, export, export_overwrite
        )
        format = CLIFormat(data_format, styles_package_identifier, export_file_ext)
        OT_CONTAINER: dict = {}
        OT_HELPER_CONTAINER: dict = {}
        _ARE_GLOBAL_PARAMETERS_READ: bool = False
        latest_registry_data: Optional[dict] = None
        latest_billing_management_factor: Optional[Union[int, float]] = None
        ignorable_teams: dict = {}
        billed_registries: dict = {}
        billing_dates = ", ".join(
            f"{year}-{month:02d}" for _, year, month in registry_files_info
        )
        registry_files_info.insert(0, registry_files_info[-1])
        logger.info(
            f"Billing will be processed for the following dates: {billing_dates}."
        )
        for registry_file_path, year, month in registry_files_info:
            year_month_date: str = f"{str(year)}-{month:02d}"
            with registry_file_path.open(mode="r") as registry_file:
                registry_data = json.load(registry_file)
            if _ARE_GLOBAL_PARAMETERS_READ is False:
                for team_id, team_registry_data in registry_data[
                    TARGET_GROUP_NAME
                ].items():
                    latest_registry_data = registry_data
                    latest_billing_management_factor = team_registry_data[
                        owners_spec.BILLING_MANAGEMENT_FACTOR
                    ]
                    if ignorable_teams.get(team_id) is None:
                        can_ignore, ignore_reason = can_ignore_team(team_registry_data)
                        if can_ignore is True:
                            ignorable_teams[team_id] = ignore_reason
                            logger.info(
                                f"Team '{team_id}' is eligible for billing, but will not be added to the "
                                f"output table for the entire given period "
                                f"for the following reason: {ignore_reason}. "
                                f"'{registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER}' "
                                f"will be incremented, and team will be exempted "
                                f"for the given billing period."
                            )
                            continue
                    is_management_limited, management_limit = (
                        is_billing_management_limited(team_registry_data)
                    )
                    extras = team_registry_data[registry_spec.EXTRAS]
                    try:
                        # noinspection PyStatementEffect
                        OT_CONTAINER[team_id]
                        # noinspection PyStatementEffect
                        OT_HELPER_CONTAINER[team_id]
                    except KeyError:
                        OT_CONTAINER[team_id] = get_ot_template()
                        OT_HELPER_CONTAINER[team_id] = {
                            "grand_total": 0,
                            "header_entry_no": 1,
                            "management_limit": None,
                        }
                    finally:
                        if is_management_limited is True:
                            OT_HELPER_CONTAINER[team_id]["management_limit"] = (
                                management_limit
                            )
                        if include_team_id is True:
                            OT_CONTAINER[team_id]["Team ID"] = team_id
                        OT_CONTAINER[team_id][ot_header_spec.ACCOUNT_NUMBER] = ""
                        OT_CONTAINER[team_id][ot_header_spec.DEPARTMENT] = (
                            extras[owners_spec.BILLING_INSTITUTE1] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.COMPANY] = (
                            extras[owners_spec.BILLING_INSTITUTE1] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.DEPARTMENT] = (
                            extras[owners_spec.BILLING_INSTITUTE2] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.PERSON_DEPARTMENT] = (
                            extras[owners_spec.BILLING_PERSON_GROUP] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.STREET] = (
                            extras[owners_spec.BILLING_STREET] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.POSTAL_CODE] = (
                            extras[owners_spec.BILLING_POSTAL_CODE] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.CITY] = (
                            extras[owners_spec.BILLING_CITY] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.INTERNAL_OR_EXTERNAL] = (
                            extras[owners_spec.BILLING_INT_EXT] or NAN
                        )
                        OT_CONTAINER[team_id][ot_header_spec.DATE] = (
                            f"{datum.day}. {DE_MONTHS_ONLY[datum.month - 1]} {datum.year}"
                        )
                        OT_CONTAINER[team_id][ot_header_spec.COST_CENTER_ACRONYM] = (
                            extras[owners_spec.BILLING_ACCOUNT_UNIT] or NAN
                        )
                        if extras[owners_spec.BILLING_INT_EXT] is None:
                            logger.warning(
                                f"Team '{team_id}' has global parameter '{owners_spec.BILLING_INT_EXT}' "
                                f"set to 'null' (or '{NAN}'). Value for column '{ot_header_spec.TEXT_2}' "
                                f"in output table will be left '{NAN}'."
                            )
                            OT_CONTAINER[team_id][ot_header_spec.TEXT_2] = NAN
                        else:
                            int_or_ext = team_registry_data[registry_spec.EXTRAS][
                                owners_spec.BILLING_INT_EXT
                            ].lower()
                            try:
                                OT_CONTAINER[team_id][ot_header_spec.TEXT_2] = (
                                    get_text_2(int_ext_to_bool[int_or_ext])
                                )
                            except KeyError:
                                logger.warning(
                                    f"Team '{team_id}' has global parameter '{owners_spec.BILLING_INT_EXT}' "
                                    f"set to '{int_or_ext}' which is not understood. "
                                    f"'{owners_spec.BILLING_INT_EXT}' will be left '{NAN}'."
                                )
                                OT_CONTAINER[team_id][ot_header_spec.TEXT_2] = NAN
                _ARE_GLOBAL_PARAMETERS_READ = True
                continue
            for team_id, team_registry_data in registry_data["teams"].items():
                can_exempt, exempt_reason = can_exempt_team(team_registry_data)
                if can_exempt is True and ignore_exempt is False:
                    billing_counter: int = team_registry_data[
                        registry_spec.TEAM_BILL_GENERATION_METADATA
                    ][registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER]
                    logger.info(
                        f"Team '{team_id}' is exempted from billing with "
                        f"'{registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER}': "
                        f"{billing_counter}, and will not be added to the "
                        f"output table for date {year_month_date}. "
                        f"'{registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER}' "
                        f"will remain unchanged."
                    )
                    continue
                if ignorable_teams.get(team_id) is not None:
                    _update_registry_single_team_bill_generation_metadata(
                        registry_data,
                        team_id=team_id,
                        include_status="exempt",
                        counter_status="increment",
                    )
                    billed_registries[registry_file_path] = registry_data
                    continue
                on_trial, trial_reason = is_team_on_trial(team_registry_data)
                if on_trial is True:
                    logger.info(
                        f"Team '{team_id}' is on trial for the following date {year_month_date}, "
                        f"and will not be included to output for that date, "
                        f"but will be included for other dates that are not on trial."
                    )
                    _update_registry_single_team_bill_generation_metadata(
                        registry_data,
                        team_id=team_id,
                        include_status="exempt",
                        counter_status="increment",
                    )
                    billed_registries[registry_file_path] = registry_data
                    continue
                monthly_bill: float = calculate_team_monthly_bill(
                    team_registry_data,
                    billing_management_factor=latest_billing_management_factor,
                )
                header_entry = partial(
                    get_billing_period_header_entry,
                    entry_month_no=OT_HELPER_CONTAINER[team_id]["header_entry_no"],
                )
                try:
                    OT_CONTAINER[team_id][
                        header_entry(ot_header_billing_period_spec.BILLING_TIME)
                    ] = f"{DE_MONTHS_ONLY[month - 1]} {datum.year}"
                    OT_CONTAINER[team_id][
                        header_entry(ot_header_billing_period_spec.MEMBER_COUNT)
                    ] = team_registry_data[registry_spec.TEAM_ACTIVE_MEMBER_COUNT]
                    OT_CONTAINER[team_id][
                        header_entry(ot_header_billing_period_spec.SERVICE)
                    ] = ot_fixed_texts_spec.SERVICE
                    OT_CONTAINER[team_id][
                        header_entry(ot_header_billing_period_spec.AMOUNT)
                    ] = team_registry_data[owners_spec.BILLING_UNIT_COST]
                    OT_CONTAINER[team_id][
                        header_entry(ot_header_billing_period_spec.TOTAL)
                    ] = monthly_bill if include_monthly_bill is True else ""
                except ValueError as e:
                    logger.error(e)
                    raise Exit(1)
                else:
                    OT_HELPER_CONTAINER[team_id]["grand_total"] += monthly_bill
                    OT_HELPER_CONTAINER[team_id]["header_entry_no"] += 1
                    OT_CONTAINER[team_id][ot_header_spec.GRAND_TOTAL] = (
                        OT_HELPER_CONTAINER[team_id]["grand_total"]
                    )
                    _update_registry_single_team_bill_generation_metadata(
                        registry_data,
                        team_id=team_id,
                        include_status="exempt",
                        counter_status="increment",
                    )
                    billed_registries[registry_file_path] = registry_data
        for team_id, team_feature in OT_CONTAINER.copy().items():
            if team_feature[ot_header_spec.GRAND_TOTAL] == 0:
                logger.info(
                    f"Team '{team_id}' is eligible for billing, but will not be added to the "
                    f"output table for the entire given period "
                    f"for the following reason: the calculated total sum "
                    f"'{ot_header_spec.GRAND_TOTAL}' is 0 €. "
                    f"'{registry_spec.BILL_GENERATION_METADATA_BILLING_COUNTER}' "
                    f"will be incremented, and team will be exempted "
                    f"for the given billing period."
                )
                OT_CONTAINER.pop(team_id)
                continue
            if team_feature[ot_header_spec.GRAND_TOTAL] == "":
                logger.info(
                    f"Team '{team_id}' does not have a numerical value for "
                    f"'{ot_header_spec.GRAND_TOTAL}' which likely means that "
                    f"the team is exempted for the entire given period. "
                    f"Team will be left out of the output table."
                )
                OT_CONTAINER.pop(team_id)
                continue
            if (
                management_limit := OT_HELPER_CONTAINER[team_id]["management_limit"]
            ) is not None:
                if team_feature[ot_header_spec.GRAND_TOTAL] > management_limit:
                    logger.info(
                        f"Team '{team_id}' has been set "
                        f"'{owners_spec.BILLING_MANAGEMENT_LIMIT}' to {management_limit} €, "
                        f"and '{ot_header_spec.GRAND_TOTAL}' {team_feature[ot_header_spec.GRAND_TOTAL]} € "
                        f"has exceeded the limit. "
                        f"{owners_spec.BILLING_MANAGEMENT_LIMIT} value will be used "
                        f"for {ot_header_spec.GRAND_TOTAL}. "
                    )
                    for period in range(1, BILLING_PERIOD + 2):
                        OT_CONTAINER[team_id][
                            get_billing_period_header_entry(
                                ot_header_billing_period_spec.MEMBER_COUNT,
                                period,
                            )
                        ] = ""
                        OT_CONTAINER[team_id][
                            get_billing_period_header_entry(
                                ot_header_billing_period_spec.AMOUNT, period
                            )
                        ] = ""
                        OT_CONTAINER[team_id][
                            get_billing_period_header_entry(
                                ot_header_billing_period_spec.TOTAL, period
                            )
                        ] = ""
                    OT_CONTAINER[team_id][ot_header_spec.TEXT_1] = get_text_1(
                        True,
                        latest_registry_data[TARGET_GROUP_NAME][team_id][
                            registry_spec.TEAM_NAME
                        ],
                    )
                    OT_CONTAINER[team_id][ot_header_spec.GRAND_TOTAL] = management_limit
            else:
                OT_CONTAINER[team_id][ot_header_spec.TEXT_1] = get_text_1(
                    False,
                    latest_registry_data[TARGET_GROUP_NAME][team_id][
                        registry_spec.TEAM_NAME
                    ],
                )
        if dry_run is False:
            for registry_file_path, registry_data in billed_registries.items():
                modify_registry_file(registry_file_path, registry_data)
        formatted_ot = format(list(OT_CONTAINER.values()))
        if export is not None:
            export_teams = Export(
                export_dest,
                file_name_stub=OUTPUT_TABLE_FILE_NAME_STUB,
                file_extension=format.convention,
                format_name=format.name,
            )
            export_teams(data=formatted_ot, verbose=True)
        else:
            if highlight_syntax is True:
                highlight = Highlight(
                    format.name, package_identifier=styles_package_identifier
                )
                stdout_console.print(highlight(formatted_ot))
            else:
                typer.echo(formatted_ot)
