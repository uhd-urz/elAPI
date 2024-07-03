from json import JSONDecodeError
from typing import Union, Iterable, Optional

import httpx

from ..core_validators import Validator, RuntimeValidationError, CriticalValidationError
from ..styles import stdin_console
from ..styles.highlight import NoteText


class HostIdentityValidator(Validator):
    __slots__ = ()

    def __init__(self, restrict_to: Union[str, Iterable[str], None] = None):
        self.restrict_to = restrict_to

    @property
    def restrict_to(self) -> Iterable[str]:
        return self._restrict_to

    @restrict_to.setter
    def restrict_to(self, value):
        if value is None:
            self._restrict_to = None
        elif isinstance(value, str):
            self._restrict_to = [value]
        elif isinstance(value, Iterable):
            self._restrict_to = value
        else:
            raise AttributeError(
                "restrict_to must be a string of target host URL, or an iterable of strings where "
                f"each string is a host URL that {HostIdentityValidator.__name__} validation will be restricted to."
            )

    @staticmethod
    def check_endpoint():
        from ..api import GETRequest

        session = GETRequest()
        return session(endpoint_name="apikeys", endpoint_id=None)

    def validate(self):
        from ..loggers import Logger
        from ..configuration import get_active_host, get_active_api_token
        from ..configuration import KEY_HOST

        logger = Logger()
        host = get_active_host()
        api_token = get_active_api_token()
        if self.restrict_to is not None:
            if host not in self.restrict_to:
                logger.error(
                    f"Detected '{KEY_HOST.lower()}' is different from the restricted host. "
                    f"'{KEY_HOST.lower()}' could not be validated!"
                )
                try:
                    stdin_console.print(
                        NoteText(
                            f"Detected '{KEY_HOST.lower()}': '{host}'. "
                            f"Host(s) restricted by {HostIdentityValidator.__name__}: '{', '.join(self.restrict_to)}'."
                        )
                    )
                except TypeError as e:
                    raise ValueError(
                        f"An invalid value might have been given to restrict_to "
                        f"attribute of {HostIdentityValidator.__name__}. Validation could not be completed!"
                    ) from e
                raise CriticalValidationError

        API_TOKEN_MASKED = api_token
        try:
            response: httpx.Response = self.check_endpoint()
            response.json()
        except (httpx.HTTPError, JSONDecodeError) as error:
            logger.critical(
                f"There was a problem accessing host '{host}' with API token '{API_TOKEN_MASKED}'."
            )
            try:
                # noinspection PyUnboundLocalVariable
                logger.info(
                    f"Returned response: '{response.status_code}: {response.text}'"
                )
            except UnboundLocalError:
                logger.info(
                    f"No request was made to the host URL! Exception details: '{error!r}'"
                )
                raise RuntimeValidationError
            if response.is_server_error:
                logger.critical(
                    f"There was a problem with the host server: '{host}'. "
                    f"Please contact an administrator."
                )
                raise RuntimeValidationError
            stdin_console.print(
                NoteText(
                    "There is likely nothing wrong with the host server. "
                    "Possible reasons for failure:\n"
                    "• Invalid/expired/incorrect API token\n"
                    "• Incorrect host URL\n",
                )
            )
            raise RuntimeValidationError


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

        logger = Logger()
        try:
            session = GETRequest(keep_session_open=True)
            caller_data: dict = session(endpoint_name="users", endpoint_id="me").json()
        except (httpx.HTTPError, JSONDecodeError):
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
        from ..loggers import Logger

        logger = Logger()
        if self.can_write:
            try:
                _session = GETRequest()
                api_token_data: Optional[dict] = _session(
                    endpoint_name="apikeys", endpoint_id="me"
                ).json()[0]
            except (httpx.HTTPError, JSONDecodeError):
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
