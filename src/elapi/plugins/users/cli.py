import re
from datetime import datetime
from typing import Annotated, Optional

import typer
from dateutil import parser

from ...api import FixedEndpoint
from ...api.validators import (
    APITokenRWValidator,
    HostIdentityValidator,
    PermissionValidator,
)
from ...core_validators import Exit, RuntimeValidationError, Validate
from ...loggers import Logger
from ...plugins.commons.cli_helpers import Typer
from ...styles import print_typer_error, stderr_console, stdout_console
from ...utils import UnexpectedAPIResponseType
from ...utils.typer_patches import patch_typer_flag_value
from ..commons import get_team_members
from .expire import (
    ExpiringTeamWithInvalidConditionException,
    TeamIdentity,
    TeamMemberNotUniqueException,
    _validate_team_for_expiry,
    _validate_teams_with_non_unique_members,
)

logger = Logger()

patch_typer_flag_value()
app = Typer(name="users", help="Manage users.")


@app.command("expire", short_help="Expire a team.")
def expire(
    date: Annotated[
        str,
        typer.Option(
            "--date",
            "-d",
            help="New expiration date for all members.",
            show_default=False,
        ),
    ],
    team_id: Annotated[
        Optional[str],
        typer.Option(
            "--team-id",
            "-i",
            help="Target team ID. Either team ID or team name must be passed.",
            show_default=False,
        ),
    ] = None,
    team_name: Annotated[
        Optional[str],
        typer.Option(
            "--team-name",
            "-n",
            help="Target team name to expire. Either team ID or team name must be passed.",
            show_default=False,
        ),
    ] = None,
    force_multi_team: Annotated[
        bool,
        typer.Option(
            "--force-multi-team",
            help="Force expiration of users that belong to more than one team.",
            show_default=False,
        ),
    ] = False,
    silent: Annotated[
        bool,
        typer.Option("--silent", help="Skip user confirmation.", show_default=False),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simulate the expiration process. --dry-run will still validate the host, API token read/write access etc.",
            show_default=False,
        ),
    ] = False,
):
    if team_id is None and team_name is None:
        print_typer_error("Either --team_id or --team_name must be provided.")
        raise Exit(1)
    try:
        target_date: datetime = parser.isoparse(date.strip())
    except ValueError as e:
        print_typer_error(f"'--date' is given an invalid ISO 8601 date '{date}'.")
        raise Exit(1) from e
    else:
        if not re.match(r"^\d+-\d{2}-\d{2}$", target_date_ := str(target_date.date())):
            print_typer_error(
                "'--date' is valid ISO 8601, but it must also be "
                "in 'YYYY-MM-DD' format."
            )
            raise Exit(1)
        with stderr_console.status(
            "Validating...\n", refresh_per_second=15
        ) as validation_status:
            validate = Validate(
                HostIdentityValidator(),
                PermissionValidator("sysadmin"),
                APITokenRWValidator(),
            )
            try:
                validate()
            except RuntimeValidationError as e:
                validation_status.stop()
                raise e
            except UnexpectedAPIResponseType as unex_exc:
                validation_status.stop()
                logger.critical(f"Unexpected API response: {unex_exc}")
                raise Exit(1) from unex_exc
        with stdout_console.status("Fetching teams and users data..."):
            teams2users_data = get_team_members(
                (users_endpoint := FixedEndpoint("users")).get().json(),
                FixedEndpoint("teams").get().json(),
            )
        try:
            with stdout_console.status("Validating team..."):
                target_team_info = _validate_team_for_expiry(
                    teams2users_data,
                    target_team=TeamIdentity(
                        target=team_id or team_name,  # type: ignore[arg-type]
                        kind="id" if team_id is not None else "name",
                    ),
                )
        except ExpiringTeamWithInvalidConditionException as inv_team_exc:
            logger.error(inv_team_exc)
            raise Exit(1)
        else:
            try:
                _validate_teams_with_non_unique_members(
                    teams2users_data, team_info=target_team_info
                )
            except TeamMemberNotUniqueException as non_unique_exc:
                if not force_multi_team:
                    logger.error(non_unique_exc)
                    raise Exit(1)
                logger.warning(non_unique_exc)
            admins_to_expire: list[str] = []
            for admin_id, admin_info in target_team_info["admins"].items():
                admins_to_expire.append(
                    f"{admin_info['firstname']} {admin_info['lastname']} (user ID: {admin_id})"
                )
            logger.info(
                f"Team '{target_team_info['team_name']}' (team ID: {target_team_info['team_id']}) has "
                f"been validated for expiration to date {target_date_}."
            )
            stdout_console.print(f"""
[b yellow]Team name:[/b yellow] {target_team_info["team_name"]}
[b yellow]Team ID:[/b yellow] {target_team_info["team_id"]}
[b yellow]Team creation date:[/b yellow] {target_team_info["team_created_at"]}
[b yellow]Total member count:[/b yellow] {target_team_info["total_member_count"]}
[b yellow]Total archived member count:[/b yellow] {target_team_info["total_archived_member_count"]}
[b yellow]Total expired member count (so far):[/b yellow] {target_team_info["total_expired_member_count"]}
[b green]Admin(s):[/b green] {", ".join(admins_to_expire)}
""")
            if not silent:
                stdout_console.print(
                    "Are you sure you want to expire team "
                    f"'{target_team_info['team_name']}' (team ID: {target_team_info['team_id']}) "
                    f"to date {target_date_}?"
                )
                can_expire_team = typer.confirm("")
            else:
                can_expire_team = True
            if can_expire_team:
                for member_id, member_info in target_team_info["members"].items():
                    if not dry_run:
                        request = users_endpoint.patch(
                            sub_endpoint_id=member_id,
                            data={"valid_until": target_date_},
                        )
                        is_request_successful = request.is_success
                    else:
                        is_request_successful = True
                    if is_request_successful:
                        logger.info(
                            f"Member '{member_info['firstname']} {member_info['lastname']}' "
                            f"(ID: {member_id}) has been expired."
                        )
                    else:
                        # noinspection PyUnboundLocalVariable
                        # This condition will never be reached if --dry-run is passed,
                        # hence the noinspection.
                        logger.error(
                            f"Could not expire member '{member_info['firstname']} "
                            f"{member_info['lastname']}' (ID: {member_id}). Response status "
                            f"code: {request.status_code}. Response body: {request.text}."
                        )
                        raise Exit(1)
                if not dry_run:
                    logger.success(
                        f"All team members of team '{target_team_info['team_name']} (team ID: "
                        f"{target_team_info['team_id']}) have been expired."
                    )
                else:
                    logger.info("Dry running team expiration process is complete.")
            else:
                logger.info("User aborted the expiration process.")
                raise Exit(0)
