import re
from datetime import datetime
from typing import Annotated, Optional

import typer
from dateutil import parser

from ...api import FixedEndpoint
from ...core_validators import Exit
from ...loggers import Logger
from ...plugins.commons.cli_helpers import Typer
from ...styles import print_typer_error, stdout_console
from ...utils.typer_patches import patch_typer_flag_value
from ..commons import get_team_members
from .expire import (
    ExpiringTeamWithInvalidConditionException,
    TeamIdentity,
    _validate_team_for_expiry,
)

logger = Logger()

patch_typer_flag_value()
app = Typer(name="users", help="Manage users.")


@app.command("expire", short_help="Expire a team.")
def expire(
    date: Annotated[
        str, typer.Option("--date", "-d", help="New expiry date.", show_default=False)
    ],
    team_id: Annotated[
        Optional[str],
        typer.Option("--team-id", "-i", help="Team ID.", show_default=False),
    ] = None,
    team_name: Annotated[
        Optional[str],
        typer.Option("--team-name", "-n", help="Team Name.", show_default=False),
    ] = None,
    silent: Annotated[
        bool,
        typer.Option("--silent", help="Skip confirmation.", show_default=False),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Simulate expiring.", show_default=False),
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
        with stdout_console.status("Fetching teams and users data..."):
            teams2users_data = get_team_members(
                (users_endpoint := FixedEndpoint("users")).get().json(),
                (teams_endpoint := FixedEndpoint("teams")).get().json(),
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
                    logger.info("Dry running is complete.")
            else:
                logger.info("User aborted the expiration process.")
                raise Exit(0)
