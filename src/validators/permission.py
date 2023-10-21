import typer
from httpx import Response

from src.loggers import Logger
from src.validators.base import Validator
from src.validators.identity import COMMON_NETWORK_ERRORS

logger = Logger()


class PermissionValidator(Validator):
    __slots__ = "_group", "team_id", "_who"

    def __init__(self, _group: str, team_id: int = 1):
        super().__init__()
        self.group: str = _group
        self.team_id = team_id

    @property
    def GROUPS(self) -> dict:
        # Default (all) permission groups.
        # Reference: https://github.com/elabftw/elabftw/blob/master/src/enums/Usergroup.php
        return {"sysadmin": 1, "admin": 2, "user": 4}

    @GROUPS.setter
    def GROUPS(self, value):
        raise AttributeError("Groups cannot be modified!")

    @property
    def group(self) -> str:
        return self._who

    @group.setter
    def group(self, value: str):
        value = value.lower()

        try:
            self.GROUPS[value]
        except KeyError:
            raise ValueError("Supported values are: 'sysadmin', 'admin', 'user'.")
        else:
            self._who = value

    @staticmethod
    def check_endpoint():
        from src.api import GETRequest

        session = GETRequest()
        return session(endpoint="users", unit_id="me")

    def validate(self) -> None:
        try:
            response: Response = self.check_endpoint()
            caller_data: dict = response.json()
        except COMMON_NETWORK_ERRORS:
            logger.critical(
                "Something went wrong while trying to read user information! "
                "Try to validate the configuration first with 'HostIdentityValidator' "
                "to see what specifically went wrong."
            )
            raise typer.Exit(1)
        else:
            if self.group == "sysadmin":
                if not caller_data["is_sysadmin"]:
                    logger.critical(
                        "Requesting user doesn't have elabftw 'sysadmin' permission "
                        "to be able to access the resource."
                    )
                    raise typer.Exit(1)
            elif self.group in ["admin", "user"]:
                for team in caller_data["teams"]:
                    if not team["id"] == self.team_id:
                        logger.critical(
                            f"The provided team ID '{self.team_id}' didn't match "
                            f"any of the teams the user is part of."
                        )
                        raise typer.Exit(1)
                    if team["usergroup"] not in [
                        self.GROUPS[self.group],
                        self.GROUPS["sysadmin"],
                    ]:
                        logger.critical(
                            f"Requesting user doesn't belong to the permission group '{self.group}'!"
                        )
                        raise typer.Exit(1)
