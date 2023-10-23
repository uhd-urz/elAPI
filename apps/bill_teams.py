from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from dateutil import parser
from dateutil.relativedelta import relativedelta
from rich.progress import track


class UsersInformation:
    __slots__ = ("users", "user_id_prefix")
    unit_name = "users"
    unit_id_prefix = "userid"

    @classmethod
    async def items(cls):
        import asyncio
        from src.endpoint import FixedEndpoint, RecursiveEndpoint

        users_endpoint = FixedEndpoint(unit_name=cls.unit_name, keep_session_open=True)
        users = await users_endpoint.json(
            unit_id=None
        )  # None gives a list of all users
        recursive_users = RecursiveEndpoint(
            users, cls.unit_id_prefix, target_endpoint=users_endpoint
        )
        tasks = [item for item in recursive_users.items()]
        recursive_users_data = [
            await task
            for task in track(
                asyncio.as_completed(tasks),
                description="Getting users_endpoint data:",
                total=len(tasks),
            )
        ]
        await users_endpoint.session.close()
        return recursive_users_data


class TeamsInformation:
    __slots__ = "teams"
    unit_name = "teams"

    @classmethod
    def items(cls) -> list[dict, ...]:
        from src.api import GETRequest

        teams = GETRequest()
        return teams(endpoint=cls.unit_name, unit_id=None).json()


@dataclass(slots=True)
class BillTeams:
    users_information: list[dict, ...]
    teams_information: list[dict, ...]
    launch_date: ClassVar[datetime] = datetime(2023, 8, 1, 0, 0, 0)
    trial_period: ClassVar[relativedelta] = relativedelta(months=6)

    def team_trial_start_date(self, creation_date: datetime) -> datetime:
        if creation_date < self.launch_date:
            return self.launch_date
        return creation_date

    def _get_owners(self) -> dict:
        # Generate teams information with team owners
        team_members, team_owners = {}, {}
        for u in self.users_information:
            for team in u["teams"]:  # O(n^2): u["teams"] is again an iterable!
                # Get teams user count
                if not team_members.get(team["id"]):
                    team_members[team["id"]]: list = [u["userid"]]
                else:
                    team_members[team["id"]].append(u["userid"])
                # Get owners information
                if team["is_owner"] == 1:
                    uid = u["userid"]
                    owner = {uid: {}}
                    owner[uid]["owner_name"] = u["fullname"]
                    owner[uid]["owner_email"] = u["email"]
                    owner[uid]["owner_user_id"] = uid
                    # duplicate information to avoid ambiguity
                    if not team_owners.get(team["id"]):
                        team_owners[team["id"]] = {}
                        team_owners[team["id"]]["team_name"] = team["name"]
                        team_owners[team["id"]]["owners"] = [owner]
                        team_owners[team["id"]]["team_id"] = team["id"]
                        # duplicate information to avoid ambiguity
                    else:
                        team_owners[team["id"]]["owners"].append(owner)

        # Add team creation date to team_owners
        for team in self.teams_information:
            if team["id"] in team_owners.keys():
                team_owners[team["id"]]["team_created_at"] = team["created_at"]

        # Add member count to team_owners
        for team_id in team_owners:
            team_owners[team_id]["members"] = {}
            team_owners[team_id]["members"]["user_ids"] = team_members[team_id]
            team_owners[team_id]["members"]["member_count"] = len(team_members[team_id])
            # Add trial information
            trial_starts_at = self.team_trial_start_date(
                parser.isoparse(team_owners[team_id]["team_created_at"])
            )
            trial_ends_at = trial_starts_at + self.trial_period
            team_owners[team_id]["trial_ends_at"] = str(trial_ends_at)
            team_owners[team_id]["on_trial"] = trial_ends_at > datetime.now()

        return team_owners

    def items(self) -> dict:
        return self._get_owners()
