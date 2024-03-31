from typing import Union, Optional

from .base import Validator, RuntimeValidationError, CriticalValidationError


class PermissionValidator(Validator):
    _SYSADMIN_GROUP_KEY_NAME = "sysadmin"
    _ADMIN_GROUP_KEY_NAME = "admin"
    _USER_GROUP_KEY_NAME = "user"
    __slots__ = "_group", "_who", "_team_id"

    def __init__(
        self,
        group: str = _USER_GROUP_KEY_NAME,
        team_id: Union[int, str, None] = None,
    ):
        super().__init__()
        self.group: str = group
        self.team_id = team_id

    @property
    def GROUPS(self) -> dict:
        # Default (all) permission groups.
        # Reference: https://github.com/elabftw/elabftw/blob/master/src/enums/Usergroup.php
        return {
            PermissionValidator._SYSADMIN_GROUP_KEY_NAME: 1,
            PermissionValidator._ADMIN_GROUP_KEY_NAME: 2,
            PermissionValidator._USER_GROUP_KEY_NAME: 4,
        }

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
            raise ValueError(f"Supported values are: {', '.join(self.GROUPS.keys())}.")
        else:
            self._who = value

    @property
    def team_id(self) -> Optional[str]:
        return self._team_id

    @team_id.setter
    def team_id(self, value):
        if value is None and self.group != PermissionValidator._SYSADMIN_GROUP_KEY_NAME:
            raise AttributeError(
                f"A team ID must be provided to {self.__class__.__name__} class "
                f"if the group to validate is not '{PermissionValidator._SYSADMIN_GROUP_KEY_NAME}'!"
            )
        self._team_id = str(value) if value is not None else value

    def validate(self) -> None:
        from ..api import GETRequest
        from ..loggers import Logger
        from .identity import COMMON_NETWORK_ERRORS, HostIdentityValidator

        logger = Logger()
        try:
            session = GETRequest(keep_session_open=True)
            caller_data: dict = session(endpoint_name="users", endpoint_id="me").json()
        except COMMON_NETWORK_ERRORS:
            logger.critical(
                "Something went wrong while trying to read user information! "
                f"Try to validate the configuration first with '{HostIdentityValidator.__name__}' "
                "to see what specifically went wrong."
            )
            raise RuntimeValidationError
        else:
            if self.group == PermissionValidator._SYSADMIN_GROUP_KEY_NAME:
                if not caller_data["is_sysadmin"]:
                    logger.critical(
                        f"Requesting user doesn't have eLabFTW '{self.group}' permission "
                        f"to be able to access the resource."
                    )
                    raise CriticalValidationError
            if self.team_id is not None:
                for team in caller_data["teams"]:
                    if str(team["id"]) == self.team_id:
                        if (
                            team["usergroup"] > self.GROUPS[self.group]
                            and self.group
                            != PermissionValidator._SYSADMIN_GROUP_KEY_NAME
                        ):  # "sysadmin" has access to all teams, hence we don't check if "sysadmin" belongs to a team.
                            logger.critical(
                                f"Requesting user is part of the team '{self.team_id}' but "
                                f"doesn't belong to the permission group '{self.group}'!"
                            )
                            raise CriticalValidationError
                        return
                logger.critical(
                    f"Requesting user is not part of the given team with team ID '{self.team_id}'!"
                )
                raise CriticalValidationError


class APITokenRWValidator(Validator):
    def __init__(self, can_write: bool = True):
        super().__init__()
        self.can_write = can_write

    def validate(self):
        from ..api import GETRequest
        from .identity import COMMON_NETWORK_ERRORS, HostIdentityValidator
        from ..loggers import Logger

        logger = Logger()
        if self.can_write:
            try:
                _session = GETRequest()
                api_token_data: Optional[dict] = _session(
                    endpoint_name="apikeys", endpoint_id="me"
                ).json()[0]
            except COMMON_NETWORK_ERRORS:
                logger.critical(
                    "Something went wrong while trying to read API token information! "
                    f"Try to validate the configuration first with '{HostIdentityValidator.__name__}' "
                    "to see what specifically went wrong."
                )
                raise RuntimeValidationError
            else:
                if not api_token_data["can_write"]:
                    logger.critical(
                        "Requesting user's API token doesn't have write permission!"
                    )
                    raise CriticalValidationError
