from dataclasses import dataclass
from functools import partial
from json import JSONDecodeError
from typing import ClassVar

from httpx import Response, UnsupportedProtocol, ConnectError, ConnectTimeout

from src._api import elabftw_fetch
from src._config_handler import records, HOST, API_TOKEN
from src.loggers import logger

network_errors: (Exception, ...) = JSONDecodeError, UnsupportedProtocol, ConnectError, ConnectTimeout, TimeoutError


@dataclass(slots=True)
class ConfigValidator:
    client: partial = partial(elabftw_fetch, endpoint="apikeys")
    _HOST_EXAMPLE: ClassVar[str] = "host: 'https://demo.elabftw.net/api/v2'"

    def validate(self):
        try:
            records.inspect_applied_config["HOST"]
        except KeyError:
            raise SystemExit(
                f"Host is missing from the config files! Host contains the URL of the root API endpoint. Example:\n"
                f"{ConfigValidator._HOST_EXAMPLE}")
        else:
            if not HOST:
                raise SystemExit(f"Host is detected but it's empty! Host contains the URL of the root API endpoint. "
                                 f"Example: {ConfigValidator._HOST_EXAMPLE}")

        try:
            records.inspect_applied_config["API_TOKEN"]
        except KeyError:
            raise SystemExit(
                "API token is missing from the config files! An API token with at least read-access is required "
                "to make requests.")
        else:
            if not API_TOKEN:
                raise SystemExit(
                    "API token is detected but it's empty! An API token with at least read-access is required "
                    "to make requests.")

            API_TOKEN_MASKED = records.inspect_applied_config.get("API_TOKEN_MASKED")[0]
            try:
                api_token_client: Response = self.client()
                api_token_client.json()
            except network_errors as error:
                logger.critical(f"There was a problem accessing host '{HOST}' with API token '{API_TOKEN_MASKED}'.")

                try:
                    # noinspection PyUnboundLocalVariable
                    logger.info(f"Returned response: '{api_token_client.status_code}: {api_token_client.text}'")
                except UnboundLocalError:
                    logger.info(f"No request was made to the host URL! Exception details: '{error!r}'")
                    raise SystemExit()

                if api_token_client.is_server_error:
                    logger.critical(
                        f"There was a problem with the host server: '{HOST}'. Please contact an administrator.")
                    raise SystemExit()
                raise SystemExit("\nThere is likely nothing wrong with the host server. Possible reasons for failure:\n"
                                 "- Invalid/expired/incorrect API token.\n"
                                 "- Incorrect host URL.\n")


class PermissionValidator:
    __slots__ = "client", "_who", "team_id"

    def __init__(self, _group: str, team_id: int = 1):
        self.group: str = _group
        self.team_id = team_id
        self.client: partial = partial(elabftw_fetch, endpoint="users", unit_id="me")

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

    def validate(self) -> None:
        try:
            user_client: Response = self.client()
            user_data: dict = user_client.json()
        except network_errors:
            logger.critical("Something went wrong while trying to read user information! "
                            "Try to validate the configuration first with 'ConfigValidator' "
                            "to see what specifically went wrong.")
            raise SystemExit()
        else:
            if self.group == "sysadmin":
                if not user_data["is_sysadmin"]:
                    logger.critical(
                        "Requesting user doesn't have elabftw 'sysadmin' permission to be able to access the resource.")
                    raise SystemExit()
            elif self.group in ["admin", "user"]:
                for team in user_data["teams"]:
                    if not team["id"] == self.team_id:
                        logger.critical(
                            f"The provided team ID '{self.team_id}' didn't match any of the teams the user is part of.")
                        raise SystemExit()
                    if not team["usergroup"] in [self.GROUPS[self.group], self.GROUPS["sysadmin"]]:
                        logger.critical(f"Requesting user doesn't belong to the permission group '{self.group}'!")
                        raise SystemExit()


class Validate:
    def __init__(self, *_typ: (ConfigValidator, PermissionValidator, ...)):
        self.typ = _typ

    def __call__(self):
        for typ in self.typ:
            typ.validate()
