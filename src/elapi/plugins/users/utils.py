from typing import Literal

from pydantic import BaseModel, field_validator

from .exceptions import DuplicateTeamNameFoundException, TeamNotFoundException
from ..commons import TeamsDict


class TeamIdentity(BaseModel):
    target: str
    kind: Literal["id", "name"]

    @field_validator("target", mode="before")
    @classmethod
    def clean_target(cls, v: str) -> str:
        return v.strip()


def _validate_team(
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
