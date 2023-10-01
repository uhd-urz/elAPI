import sys
from abc import ABC, abstractmethod
from json import JSONDecodeError

import typer
from httpx import Response, UnsupportedProtocol, ConnectError, ConnectTimeout, InvalidURL

from src.api import GETRequest
from src.config import records, HOST, API_TOKEN
from src.loggers import Logger

logger = Logger()


class Validator(ABC):
    def __init__(self):
        self._common_network_errors: tuple = (JSONDecodeError, UnsupportedProtocol, InvalidURL,
                                              ConnectError, ConnectTimeout, TimeoutError)

    @abstractmethod
    def check_endpoint(self, **kwargs):
        try:
            endpoint, unit_id = kwargs["endpoint"], kwargs["unit_id"]
        except KeyError:
            return NotImplemented
        else:
            session = GETRequest()
            return session(endpoint, unit_id)

    @abstractmethod
    def validate(self):
        ...

    @property
    def common_network_errors(self):
        return self._common_network_errors

    @common_network_errors.setter
    def common_network_errors(self, value):
        if value not in self._common_network_errors:
            self._common_network_errors += value
        else:
            raise ValueError(f"Value {value} already exists!")

    @common_network_errors.deleter
    def common_network_errors(self):
        self._common_network_errors = ()


class ConfigValidator(Validator):
    __slots__ = ()

    def check_endpoint(self):
        return super().check_endpoint(endpoint="apikeys", unit_id="")

    def validate(self):
        _HOST_EXAMPLE: str = "host: 'https://demo.elabftw.net/api/v2'"

        try:
            records.inspect_applied_config["HOST"]
        except KeyError:
            print(f"Host is missing from the config files! Host contains the URL of the root API endpoint. Example:"
                  f"\n{_HOST_EXAMPLE}", file=sys.stderr)
            raise typer.Exit(1)
        else:
            if not HOST:
                print(f"Host is detected but it's empty! Host contains the URL of the root API endpoint. Example:"
                      f"\n{_HOST_EXAMPLE}", file=sys.stderr)
                raise typer.Exit(1)

        try:
            records.inspect_applied_config["API_TOKEN"]
        except KeyError:
            print("API token is missing from the config files! An API token with at least read-access is required "
                  "to make requests.", file=sys.stderr)
            raise typer.Exit(1)
        else:
            if not API_TOKEN:
                print("API token is detected but it's empty! An API token with at least read-access is required "
                      "to make requests.", file=sys.stderr)
                raise typer.Exit(1)

            API_TOKEN_MASKED = records.inspect_applied_config.get("API_TOKEN_MASKED")[0]
            try:
                response: Response = self.check_endpoint()
                response.json()
            except self.common_network_errors as error:
                logger.critical(f"There was a problem accessing host '{HOST}' with API token '{API_TOKEN_MASKED}'.")

                try:
                    # noinspection PyUnboundLocalVariable
                    logger.info(f"Returned response: '{response.status_code}: {response.text}'")
                except UnboundLocalError:
                    logger.info(f"No request was made to the host URL! Exception details: '{error!r}'")
                    raise typer.Exit(1)

                if response.is_server_error:
                    logger.critical(
                        f"There was a problem with the host server: '{HOST}'. Please contact an administrator.")
                    raise typer.Exit(1)
                print("\nThere is likely nothing wrong with the host server. Possible reasons for failure:\n"
                      "- Invalid/expired/incorrect API token.\n"
                      "- Incorrect host URL.\n", file=sys.stderr)
                raise typer.Exit(1)


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

    def check_endpoint(self):
        return super().check_endpoint(endpoint="users", unit_id="me")

    def validate(self) -> None:
        try:
            response: Response = self.check_endpoint()
            caller_data: dict = response.json()
        except self.common_network_errors:
            logger.critical("Something went wrong while trying to read user information! "
                            "Try to validate the configuration first with 'ConfigValidator' "
                            "to see what specifically went wrong.")
            raise typer.Exit(1)
        else:
            if self.group == "sysadmin":
                if not caller_data["is_sysadmin"]:
                    logger.critical(
                        "Requesting user doesn't have elabftw 'sysadmin' permission to be able to access the resource.")
                    raise typer.Exit(1)
            elif self.group in ["admin", "user"]:
                for team in caller_data["teams"]:
                    if not team["id"] == self.team_id:
                        logger.critical(
                            f"The provided team ID '{self.team_id}' didn't match any of the teams the user is part of.")
                        raise typer.Exit(1)
                    if not team["usergroup"] in [self.GROUPS[self.group], self.GROUPS["sysadmin"]]:
                        logger.critical(f"Requesting user doesn't belong to the permission group '{self.group}'!")
                        raise typer.Exit(1)


class Validate:
    def __init__(self, *_typ: (ConfigValidator, PermissionValidator, ...)):
        self.typ = _typ

    def __call__(self):
        for typ in self.typ:
            typ.validate()
