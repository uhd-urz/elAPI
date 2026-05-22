from typing import Literal, Optional, TypedDict

import yaml
from pydantic import BaseModel, field_validator

from ..._vendor.haggis.logs import add_logging_level
from ..commons import TeamsDict

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


class TeamIdentity(BaseModel):
    target: str
    kind: Literal["id", "name"]

    @field_validator("target", mode="before")
    @classmethod
    def clean_target(cls, v: str) -> str:
        return v.strip()


class ExpiringTeamWithInvalidConditionException(Exception): ...


class DuplicateTeamNameFoundException(ExpiringTeamWithInvalidConditionException): ...


class TeamNotFoundException(ExpiringTeamWithInvalidConditionException): ...


class TeamMemberNotUniqueException(Exception): ...


def _get_team_names_from_ids(
    teams2users_data: dict[str, TeamsDict], team_ids: list[str]
) -> list[str]:
    team_names: list[str] = []
    for id_ in team_ids:
        team_names.append(f"{teams2users_data[id_]['team_name']} (team ID: {id_})")
    return team_names


def _validate_team_for_expiry(
    teams2users_data: dict[str, TeamsDict], *, target_team: TeamIdentity
) -> TeamsDict:
    target_team_id = target_team.target
    match target_team.kind:
        case "name":
            _target_found: bool = False
            for _team_id, team_info in teams2users_data.items():
                if team_info["team_name"] == target_team.target:
                    target_team_id = _team_id
                    if _target_found:
                        raise DuplicateTeamNameFoundException(
                            f"More than one team is found with the same "
                            f"name '{team_info['team_name']}'. Please try with the "
                            f"team ID instead."
                        )
                    _target_found = True
            if not _target_found:
                raise TeamNotFoundException(
                    f"No team with the given name '{target_team.target}' is found."
                )
    try:
        team_info = teams2users_data[target_team_id]
    except KeyError as e:
        raise TeamNotFoundException(
            f"No team with the ID '{target_team_id}' is found."
        ) from e
    else:
        return team_info


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
