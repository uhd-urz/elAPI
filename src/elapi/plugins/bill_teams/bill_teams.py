from datetime import datetime
from pathlib import Path
from typing import Union

from dateutil import parser
from dateutil.relativedelta import relativedelta

from ...loggers import Logger
from ...path import ProperPath
from ...validators import Exit

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


class OwnersInformation:
    def __init__(self, source_path: Union[Path, ProperPath, str], delimiter: str = ";"):
        self.source_path = source_path
        self.delimiter = delimiter

    @property
    def source_path(self) -> ProperPath:
        return self._source_path

    @source_path.setter
    def source_path(self, value):
        if not isinstance(value, ProperPath):
            value = ProperPath(value, err_logger=logger)
        self._source_path = value

    def items(self) -> dict:
        import csv

        with self.source_path.open() as f:
            owners: list[dict] = list(csv.DictReader(f, delimiter=self.delimiter))
        if not owners:
            logger.error(
                f"Given source file '{self.source_path}' for "
                f"{OwnersInformation.__name__} cannot be empty!"
            )
            raise Exit(1)
        try:
            owners_flat = {}
            for team in owners:
                if not owners_flat.get(team_id := team["team_id"]):
                    owners_flat[team.pop("team_id")] = team
                    continue
                logger.warning(
                    f"Duplicate row with team ID '{team_id}' "
                    f"in source '{self.source_path}' is detected. Only the last detected column"
                    f"will be considered."
                )
        except KeyError as e:
            raise ValueError(
                f"Given source file '{self.source_path}' for "
                f"{OwnersInformation.__name__} might be invalid! Key '{e}' couldn't be found."
            ) from e
        else:
            return owners_flat


class TeamsList:
    __slots__ = "users", "teams", "contract"

    def __init__(
        self,
        users_information: list[dict, ...],
        teams_information: list[dict, ...],
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
        team_members, teams = {}, {}
        for u in self.users:
            for team in u["teams"]:  # O(n^2): u["teams"] is again an iterable!
                uid = u["userid"]
                # Get teams user count
                if not team_members.get(team["id"]):
                    team_members[team["id"]]: dict = {
                        uid: {
                            "firstname": u["firstname"],
                            "lastname": u["lastname"],
                            "email": u["email"],
                            "expired": self.is_user_expired(user_data=u),
                        }
                    }
                else:
                    team_members[team["id"]].update(
                        {
                            uid: {
                                "firstname": u["firstname"],
                                "lastname": u["lastname"],
                                "email": u["email"],
                                "expired": self.is_user_expired(user_data=u),
                            }
                        }
                    )
                # Get team basic information
                teams[team["id"]] = {}
                teams[team["id"]]["team_name"] = team["name"]
                teams[team["id"]]["team_id"] = team["id"]

        # Add team creation date to teams
        for team in self.teams:
            if team["id"] in teams.keys():
                teams[team["id"]]["team_created_at"] = team["created_at"]

        # Add member count to teams
        for team_id in teams:
            teams[team_id]["members"] = {}
            teams[team_id]["members"] = team_members[team_id]
            teams[team_id]["total_unarchived_member_count"] = len(team_members[team_id])
            teams[team_id]["active_member_count"] = 0
            for k in team_members[team_id]:
                if team_members[team_id][k]["expired"] is False:
                    teams[team_id]["active_member_count"] += 1
            # Add trial information
            trial_starts_at = self.team_trial_start_date(
                parser.isoparse(teams[team_id]["team_created_at"])
            )
            trial_ends_at = trial_starts_at + self.TRIAL_PERIOD
            teams[team_id]["trial_ends_at"] = str(trial_ends_at)
            teams[team_id]["on_trial"] = trial_ends_at > datetime.now()

        return teams

    def items(self) -> dict:
        return self._get_owners()


class OwnersList:
    __slots__ = "owners"

    def __init__(self, owners_information: dict):
        self.owners = owners_information

    def items(self) -> dict:
        team_owners: dict = {}
        for team_id, team in self.owners.items():
            team_owners[team_id] = {}
            team_owners[team_id]["owner"] = {}
            team_owners[team_id]["owner"]["team_owner_user_id"] = team[
                "team_owner_user_id"
            ]
            team_owners[team_id]["owner"]["team_owner_firstname"] = team[
                "team_owner_firstname"
            ]
            team_owners[team_id]["owner"]["team_owner_lastname"] = team[
                "team_owner_lastname"
            ]
            team_owners[team_id]["owner"]["team_owner_email"] = team["team_owner_email"]

        return team_owners
