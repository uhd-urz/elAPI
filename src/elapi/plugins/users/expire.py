from typing import Optional, TypedDict

import yaml

from .exceptions import TeamMemberNotUniqueException
from ..commons import TeamsDict
from ..._vendor.haggis.logs import add_logging_level

add_logging_level(
    "SUCCESS",
    25,
    method_name="success",
    if_exists="KEEP",
)


NonUniqueTeamMembersDict = TypedDict(
    "NonUniqueTeamMembersDict",
    {
        "Fullname": str,
        "Email": str,
        "Expires on": Optional[str],
        "Teams": str,
    },
)


def _get_team_names_from_ids(
    teams2users_data: dict[str, TeamsDict], team_ids: list[str]
) -> list[str]:
    team_names: list[str] = []
    for id_ in team_ids:
        team_names.append(f"{teams2users_data[id_]['team_name']} (team ID: {id_})")
    return team_names


def _validate_teams_with_non_unique_members(
    teams2users_data: dict[str, TeamsDict], *, team_info: TeamsDict
) -> None:
    target_team_name = team_info["team_name"]
    non_unique_members: dict[str, NonUniqueTeamMembersDict] = {}
    for member_id, member_info in team_info["members"].items():
        if len(member_info["team_member_of"]) > 1:
            non_unique_members[f"User {member_id}"] = {
                "Fullname": f"{member_info['firstname']} {member_info['lastname']}",
                "Email": member_info["email"],
                "Expires on": member_info["valid_until"],
                "Teams": (
                    ", ".join(
                        _get_team_names_from_ids(
                            teams2users_data, member_info["team_member_of"]
                        )
                    )
                ),
            }
    if non_unique_members:
        raise TeamMemberNotUniqueException(
            f"Team '{target_team_name}' (team ID: {team_info['team_id']}) has the "
            f"following members that belong to more than one team: \n"
            f"{yaml.dump(non_unique_members, indent=4, allow_unicode=True, sort_keys=False)}"
        )
    return
