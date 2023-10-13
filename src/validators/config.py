import sys

import typer
from httpx import Response

from src.loggers import Logger
from src.validators.base import Validator, COMMON_NETWORK_ERRORS

logger = Logger()


class ConfigValidator(Validator):
    __slots__ = ()

    @staticmethod
    def check_endpoint():
        from src.api import GETRequest

        session = GETRequest()
        return session(endpoint="apikeys", unit_id="")

    def validate(self):
        from src.config import inspect, HOST, API_TOKEN

        _HOST_EXAMPLE: str = "host: 'https://demo.elabftw.net/api/v2'"

        try:
            inspect.applied_config["HOST"]
        except KeyError:
            print(
                f"Host is missing from the config files! "
                f"Host contains the URL of the root API endpoint. Example:"
                f"\n{_HOST_EXAMPLE}",
                file=sys.stderr,
            )
            raise typer.Exit(1)
        else:
            if not HOST:
                print(
                    f"Host is detected but it's empty! "
                    f"Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                    file=sys.stderr,
                )
                raise typer.Exit(1)

        try:
            inspect.applied_config["API_TOKEN"]
        except KeyError:
            print(
                "API token is missing from the config files! "
                "An API token with at least read-access is required to make requests.",
                file=sys.stderr,
            )
            raise typer.Exit(1)
        else:
            if not API_TOKEN:
                print(
                    "API token is detected but it's empty! "
                    "An API token with at least read-access is required to make requests.",
                    file=sys.stderr,
                )
                raise typer.Exit(1)

            API_TOKEN_MASKED = inspect.applied_config.get("API_TOKEN")[0]
            try:
                response: Response = self.check_endpoint()
                response.json()
            except COMMON_NETWORK_ERRORS as error:
                logger.critical(
                    f"There was a problem accessing host '{HOST}' with API token '{API_TOKEN_MASKED}'."
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
                    raise typer.Exit(1)

                if response.is_server_error:
                    logger.critical(
                        f"There was a problem with the host server: '{HOST}'. "
                        f"Please contact an administrator."
                    )
                    raise typer.Exit(1)
                print(
                    "\nThere is likely nothing wrong with the host server. "
                    "Possible reasons for failure:\n"
                    "- Invalid/expired/incorrect API token.\n"
                    "- Incorrect host URL.\n",
                    file=sys.stderr,
                )
                raise typer.Exit(1)
