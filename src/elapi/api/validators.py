from enum import IntEnum
from json import JSONDecodeError
from typing import Iterable, Optional, Union

import httpx

from ..api import GETRequest
from ..configuration import KEY_HOST, get_active_api_token, get_active_host
from ..core_validators import CriticalValidationError, RuntimeValidationError, Validator
from ..loggers import Logger
from ..styles import stdout_console
from ..styles.highlight import NoteText

logger = Logger()


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
                "restrict_to must be a string of target host URL, "
                "or an iterable of strings where "
                f"each string is a host URL that {HostIdentityValidator.__name__} "
                f"validation will be restricted to."
            )

    def validate(self):
        host = get_active_host()
        api_token = get_active_api_token()
        if self.restrict_to is not None:
            if host not in self.restrict_to:
                logger.error(
                    f"Detected '{KEY_HOST.lower()}' is different from the restricted host. "
                    f"'{KEY_HOST.lower()}' could not be validated!"
                )
                try:
                    stdout_console.print(
                        NoteText(
                            f"Detected '{KEY_HOST.lower()}': '{host}'. "
                            f"Host(s) restricted by {HostIdentityValidator.__name__}: "
                            f"'{', '.join(self.restrict_to)}'."
                        )
                    )
                except TypeError as e:
                    raise ValueError(
                        f"An invalid value might have been given to restrict_to "
                        f"attribute of {HostIdentityValidator.__name__}. "
                        f"Validation could not be completed!"
                    ) from e
                raise CriticalValidationError

        api_token_masked = api_token
        try:
            session = GETRequest()
            response: httpx.Response = session(endpoint_name="apikeys")
        except httpx.HTTPError as e:
            logger.critical(
                f"There was a problem accessing host '{host}' with API token "
                f"'{api_token_masked}'. No request was made. "
                f"Exception details: {e!r}"
            )
            raise RuntimeValidationError
        else:
            try:
                response.json()
            except JSONDecodeError as error:
                logger.error(
                    f"Returned response from host '{host}' could not be parsed as JSON. "
                    f"JSON exception details: {error!r}."
                    f"Response status: {response.status_code}. "
                    f"Response: {response.text}"
                )
                if response.is_server_error:
                    logger.critical(
                        f"There was a problem with the host server: '{host}'. "
                        f"Please contact an administrator."
                    )
                    raise RuntimeValidationError
                stdout_console.print(
                    NoteText(
                        "There is likely nothing wrong with the host server. "
                        "Possible reasons for failure:\n"
                        "• Invalid/expired/incorrect API token\n"
                        "• Incorrect host URL\n",
                    )
                )
                raise RuntimeValidationError


class ElabUserGroups(IntEnum):
    """eLabFTW's default permission groups.
    See: https://github.com/elabftw/elabftw/blob/master/src/Enums/Usergroup.php
    """

    sysadmin = 1
    admin = 2
    user = 4

    @classmethod
    def group_names(cls) -> list[str]:
        return [_.name for _ in cls]

    @classmethod
    def group_values(cls) -> list[int]:
        return [_.value for _ in cls]


class ElabScopes(IntEnum):
    self = 1
    team = 2
    everything = 3


class PermissionValidator(Validator):
    __slots__ = "_group", "_who", "_team_id"

    def __init__(
        self,
        group: str = ElabUserGroups.user.name,
        team_id: Union[int, str, None] = None,
    ):
        super().__init__()
        self.group: str = group
        self.team_id = team_id

    @property
    def group(self) -> str:
        return self._who

    @group.setter
    def group(self, value: str):
        value = value.lower()
        try:
            ElabUserGroups[value]
        except KeyError:
            raise ValueError(
                f"Supported values are: {', '.join(ElabUserGroups.group_names())}."
            )
        else:
            self._who = value

    @property
    def team_id(self) -> Optional[str]:
        return self._team_id

    @team_id.setter
    def team_id(self, value):
        if value is None and self.group != ElabUserGroups.sysadmin.name:
            raise AttributeError(
                f"A team ID must be provided to {self.__class__.__name__} class "
                f"if the group to validate is not a "
                f"'{ElabUserGroups.sysadmin.name}' group!"
            )
        self._team_id = str(value) if value is not None else value

    def validate(self) -> None:
        try:
            session = GETRequest()
            caller_data: dict = session(endpoint_name="users", endpoint_id="me").json()
        except (httpx.HTTPError, JSONDecodeError) as e:
            logger.critical(
                "An exception occurred while trying to read user information! "
                f"Maybe configuration was not validated first? If not, "
                f"validate the configuration first with '{HostIdentityValidator.__name__}' "
                f"to see what specifically went wrong. Exception details: {e!r}"
            )
            raise RuntimeValidationError
        else:
            if self.group == ElabUserGroups.sysadmin.name:
                if not caller_data["is_sysadmin"]:
                    logger.critical(
                        f"Requesting user doesn't have eLabFTW '{self.group}' permission "
                        f"to be able to access the resource."
                    )
                    raise CriticalValidationError
            if self.team_id is not None:
                for team in caller_data["teams"]:
                    if str(team["id"]) == self.team_id:
                        if team["usergroup"] > ElabUserGroups[self.group]:
                            logger.critical(
                                f"Requesting user is part of the team '{self.team_id}' but "
                                f"doesn't belong to the permission group '{self.group}'!"
                            )
                            raise CriticalValidationError
                        return
                logger.critical(
                    f"Requesting user is not part of the given team with "
                    f"team ID '{self.team_id}'!"
                )
                raise CriticalValidationError


class APITokenRWValidator(Validator):
    def __init__(self, can_write: bool = True):
        super().__init__()
        self.can_write = can_write

    def validate(self):
        if self.can_write:
            try:
                session = GETRequest()
                api_token_data: Optional[dict] = session(
                    endpoint_name="apikeys"
                ).json()[0]
            except (httpx.HTTPError, JSONDecodeError) as e:
                logger.critical(
                    "An exception occurred while trying to read API token information! "
                    f"Maybe configuration was not validated first? If not, "
                    f"validate the configuration first with '{HostIdentityValidator.__name__}' "
                    f"to see what specifically went wrong. Exception details: {e!r}"
                )
                raise RuntimeValidationError
            else:
                if not api_token_data["can_write"]:
                    logger.critical(
                        "Requesting user's API token doesn't have write permission!"
                    )
                    raise CriticalValidationError
