from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta

from ...loggers import Logger

logger = Logger()


class UsersInformation:
    __slots__ = "users", "user_id_prefix"
    endpoint_name = "users"
    endpoint_id_key_name = "userid"

    @classmethod
    async def items(cls):
        from ..commons import RecursiveInformation

        return await RecursiveInformation(
            cls.endpoint_name, cls.endpoint_id_key_name
        ).items()


class TeamsInformation:
    __slots__ = "teams"
    endpoint_name = "teams"

    @classmethod
    def items(cls) -> list[dict, ...]:
        from ..commons import Information

        return Information(cls.endpoint_name).items()


class BillTeamsList:
    __slots__ = "users", "teams"

    def __init__(
        self, users_information: list[dict, ...], teams_information: list[dict, ...]
    ):
        self.users = users_information
        self.teams = teams_information

    @property
    def BILL_RUN_DATE(self) -> datetime:
        return datetime.now()

    @BILL_RUN_DATE.setter
    def BILL_RUN_DATE(self, value):
        raise AttributeError(
            "BILL_RUN_DATE is always the current date. It cannot be modified!"
        )

    @property
    def LAUNCH_DATE(self) -> datetime:
        return datetime(2023, 8, 1, 0, 0, 0)

    @property
    def TRIAL_PERIOD(self) -> relativedelta:
        return relativedelta(months=6)

    def team_trial_start_date(self, creation_date: datetime) -> datetime:
        if creation_date < self.LAUNCH_DATE:
            return self.LAUNCH_DATE
        return creation_date

    def is_user_expired(self, user_data: dict) -> bool:
        if (user_expiration_date := user_data["valid_until"]) is not None:
            if parser.isoparse(user_expiration_date) < self.BILL_RUN_DATE:
                return True
        return False

    def _get_owners(self) -> dict:
        # Generate teams information with team owners
        team_members, team_owners = {}, {}
        for u in self.users:
            for team in u["teams"]:  # O(n^2): u["teams"] is again an iterable!
                uid = u["userid"]
                # Get teams user count
                if not self.is_user_expired(user_data=u):
                    if not team_members.get(team["id"]):
                        team_members[team["id"]]: list = [uid]
                    else:
                        team_members[team["id"]].append(uid)
                # Get owners information
                if team["is_owner"] == 1:
                    owner = {uid: {}}
                    owner[uid]["owner_name"] = u["fullname"]
                    owner[uid]["owner_email"] = u["email"]
                    owner[uid]["owner_user_id"] = uid
                else:
                    owner = None
                # duplicate information to avoid ambiguity
                if not team_owners.get(team["id"]):
                    team_owners[team["id"]] = {}
                    team_owners[team["id"]]["team_name"] = team["name"]
                    team_owners[team["id"]]["owners"] = (
                        [owner] if owner is not None else owner
                    )
                    team_owners[team["id"]]["team_id"] = team["id"]
                else:
                    if team_owners[team["id"]]["owners"] and owner:
                        team_owners[team["id"]]["owners"].append(owner)

        # Add team creation date to team_owners
        for team in self.teams:
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
            trial_ends_at = trial_starts_at + self.TRIAL_PERIOD
            team_owners[team_id]["trial_ends_at"] = str(trial_ends_at)
            team_owners[team_id]["on_trial"] = trial_ends_at > datetime.now()

        return team_owners

    def items(self) -> dict:
        return self._get_owners()
