import asyncio
from datetime import datetime
from typing import Awaitable

import httpx
from dateutil import parser
from dateutil.relativedelta import relativedelta
from httpx import Response

from ...loggers import Logger

logger = Logger()
_RETRY_TRIGGER_ERRORS = (
    httpx.TimeoutException,
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    TimeoutError,
)


class UsersInformation:
    __slots__ = "users", "user_id_prefix"
    endpoint_name = "users"
    endpoint_id_prefix = "userid"

    @classmethod
    async def items(cls):
        from ...endpoint import FixedAsyncEndpoint, RecursiveGETEndpoint
        from rich.progress import track

        event_loop = asyncio.get_running_loop()
        users_endpoint = FixedAsyncEndpoint(endpoint_name=cls.endpoint_name)
        try:
            users = (
                await users_endpoint.get(endpoint_id=None)
            ).json()  # None gives a list of all users
            recursive_users = RecursiveGETEndpoint(
                users, cls.endpoint_id_prefix, target_endpoint=users_endpoint
            )
            tasks: list[Awaitable[Response]] = [
                item for item in recursive_users.endpoints()
            ]
            recursive_users_data: list = []

            for task in track(
                asyncio.as_completed(tasks),
                total=len(tasks),
                description=f"Getting {cls.endpoint_name} data:",
                transient=True,
            ):
                recursive_users_data.append((await task).json())
        except _RETRY_TRIGGER_ERRORS as error:
            logger.warning(
                f"Retrieving {cls.endpoint_name} data was interrupted due to a network error. "
                f"Exception details: '{error!r}'"
            )
            event_loop.set_exception_handler(lambda loop, context: ...)
            # "lambda loop, context: ..." suppresses asyncio error emission:
            # https://docs.python.org/3/library/asyncio-dev.html#detect-never-retrieved-exceptions
            await users_endpoint.close()
            if event_loop.is_running():
                event_loop.stop()  # Will raise RuntimeError
            raise InterruptedError  # This will likely never be reached,
            # since this entire exception block will only trigger while event loop is still running
        except (KeyboardInterrupt, asyncio.CancelledError):
            await users_endpoint.close()
            event_loop.stop()
            raise SystemExit(1)
        else:
            await users_endpoint.close()
            return recursive_users_data


class TeamsInformation:
    __slots__ = "teams"
    endpoint_name = "teams"

    @classmethod
    def items(cls) -> list[dict, ...]:
        from ...api import GETRequest

        teams = GETRequest()
        try:
            return teams(endpoint_name=cls.endpoint_name, endpoint_id=None).json()
        except _RETRY_TRIGGER_ERRORS:
            teams.close()
            raise InterruptedError
        except KeyboardInterrupt:
            teams.close()
            raise SystemExit(1)


class InternalTeamsInformation:
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
