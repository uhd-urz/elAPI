from collections import defaultdict
from datetime import datetime
from typing import TypedDict

from dateutil import parser

from ...api import ElabUserGroups, handle_new_user_teams


class TeamMembersDict(TypedDict, total=False):
    firstname: str
    lastname: str
    email: str
    usergroup: str
    is_archived: bool
    is_expired: bool
    valid_until: str | None
    team_member_of: list[str]


class TeamsDict(TypedDict, total=False):
    active_member_count: int
    admins: dict[str, TeamMembersDict]
    members: dict[str, TeamMembersDict]
    on_trial: bool
    team_created_at: str
    team_id: int
    team_name: str
    total_archived_member_count: int
    total_expired_member_count: int
    total_member_count: int
    total_unarchived_member_count: int
    trial_ends_at: str


def is_user_expired(
    user_data: dict | TeamMembersDict, current_date: datetime = datetime.now()
) -> bool:
    if (user_expiration_date := user_data["valid_until"]) is not None:
        if parser.isoparse(user_expiration_date) < current_date:
            return True
    return False


def get_team_members(
    users_data: list[dict],
    teams_data: list[dict],
    *,
    admins_only: bool = False,
    current_date: datetime = datetime.now(),
) -> dict[str, TeamsDict]:
    # noinspection PyTypeChecker
    team_members: defaultdict[str, dict[str, TeamMembersDict]] = defaultdict(dict)
    user_team_rel: defaultdict[str, list[str]] = defaultdict(list)
    # noinspection PyTypeChecker
    admins: defaultdict[str, dict[str, TeamMembersDict]] = defaultdict(dict)
    teams: dict[str, TeamsDict] = {}
    for u in users_data:
        user_teams = handle_new_user_teams(u["teams"])
        for user_team in user_teams:  # O(n^2): we iterate over the "teams" field
            uid = u["userid"]
            # Get teams user count
            team_id = str(user_team["id"])
            user_team_rel[uid].append(team_id)
            team_members[team_id].update(
                {
                    uid: {
                        "firstname": u["firstname"],
                        "lastname": u["lastname"],
                        "email": u["email"],
                        "usergroup": user_team["usergroup"],
                        "is_archived": bool(user_team["is_archived"]),
                        "valid_until": u["valid_until"],
                        "is_expired": is_user_expired(u, current_date),
                        "team_member_of": user_team_rel[uid],
                    }
                }
            )
            if user_team["usergroup"] == ElabUserGroups.admin:
                admins[team_id].update(
                    {
                        uid: {
                            "firstname": u["firstname"],
                            "lastname": u["lastname"],
                            "email": u["email"],
                            "usergroup": user_team["usergroup"],
                            "is_archived": bool(user_team["is_archived"]),
                            "valid_until": u["valid_until"],
                            "is_expired": is_user_expired(u, current_date),
                            "team_member_of": user_team_rel[uid],
                        }
                    }
                )
            # Get team basic information
            teams[team_id] = {}
            teams[team_id]["team_name"] = user_team["name"]
            teams[team_id]["team_id"] = user_team["id"]

    # Add team creation date to teams
    for team in teams_data:
        team_id = str(team["id"])
        if team_id in teams.keys():
            teams[team_id]["team_created_at"] = team["created_at"]

    # Add member count to teams
    for team_id in teams:
        if not admins_only:
            teams[team_id]["members"] = {}
            teams[team_id]["members"] = team_members[team_id]
        teams[team_id]["admins"] = admins.get(team_id, {})
        teams[team_id]["total_member_count"] = len(team_members[team_id])
        teams[team_id]["total_archived_member_count"] = 0
        teams[team_id]["total_expired_member_count"] = 0
        for k in team_members[team_id]:
            if team_members[team_id][k]["is_archived"]:
                teams[team_id]["total_archived_member_count"] += 1
            if team_members[team_id][k]["is_expired"]:
                teams[team_id]["total_expired_member_count"] += 1
    return teams
