from json import JSONDecodeError

import httpx

from .base import Validator, RuntimeValidationError, CriticalValidationError
from ..styles import stdin_console
from ..styles.highlight import NoteText

COMMON_NETWORK_ERRORS: tuple = (
    JSONDecodeError,
    httpx.UnsupportedProtocol,
    httpx.InvalidURL,
    httpx.TimeoutException,
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    TimeoutError,
)


class HostIdentityValidator(Validator):
    __slots__ = ()

    @staticmethod
    def check_endpoint():
        from ..api import GETRequest

        session = GETRequest()
        return session(endpoint_name="apikeys", endpoint_id=None)

    def validate(self):
        from ..loggers import Logger
        from ..configuration.config import (
            inspect,
            KEY_HOST,
            KEY_API_TOKEN,
            HOST,
            API_TOKEN,
        )

        logger = Logger()
        _HOST_EXAMPLE: str = "host: 'https://demo.elabftw.net/api/v2'"

        try:
            inspect.applied_config[KEY_HOST]
        except KeyError:
            logger.critical("'host' is missing from configuration file.")
            stdin_console.print(
                NoteText(
                    "Host is the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        else:
            if not HOST:
                logger.critical("'host' is detected on configuration file but it's empty.")
                stdin_console.print(
                    NoteText(
                        "Host contains the URL of the root API endpoint. Example:"
                        f"\n{_HOST_EXAMPLE}",
                    )
                )
                raise CriticalValidationError

        try:
            inspect.applied_config[KEY_API_TOKEN]
        except KeyError:
            logger.critical("'api_token' is missing from configuration file.")
            stdin_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests."
                )
            )
            raise CriticalValidationError
        else:
            if not API_TOKEN:
                logger.critical("'api_token' is detected on configuration file but it's empty.")
                stdin_console.print(
                    NoteText(
                        "An API token with at least read-access is required to make requests.",
                    )
                )
                raise CriticalValidationError

            API_TOKEN_MASKED = inspect.applied_config.get(KEY_API_TOKEN).value
            try:
                response: httpx.Response = self.check_endpoint()
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
                    raise RuntimeValidationError

                if response.is_server_error:
                    logger.critical(
                        f"There was a problem with the host server: '{HOST}'. "
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
