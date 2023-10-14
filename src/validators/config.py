import typer
from httpx import Response
from rich.console import Console
from rich.padding import Padding
from rich.text import Text

from src.config import KEY_HOST, KEY_API_TOKEN
from src.loggers import Logger
from src.validators.base import Validator, COMMON_NETWORK_ERRORS

logger = Logger()
console = Console()


class NoteText:
    def __new__(
        cls, text: str, /, stem: str = "P.S.", color: str = "yellow", indent: int = 3
    ):
        return Padding(
            f"{Text(f'[b {color}]{stem}:[/b {color}]')} {text}", pad=(1, 0, 0, indent)
        )


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
        # _PS: Text = Text("[b yellow]P.S.:[/b yellow]")

        try:
            inspect.applied_config[KEY_HOST]
        except KeyError:
            console.print(
                NoteText(
                    "Host is missing from the config files! "
                    "Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise typer.Exit(1)
        else:
            if not HOST:
                console.print(
                    NoteText(
                        "Host is detected but it's empty! "
                        "Host contains the URL of the root API endpoint. Example:"
                        f"\n{_HOST_EXAMPLE}",
                    )
                )
                raise typer.Exit(1)

        try:
            inspect.applied_config[KEY_API_TOKEN]
        except KeyError:
            console.print(
                NoteText(
                    "API token is missing from the config files! "
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise typer.Exit(1)
        else:
            if not API_TOKEN:
                console.print(
                    NoteText(
                        "API token is detected but it's empty! "
                        "An API token with at least read-access is required to make requests.",
                    )
                )
                raise typer.Exit(1)

            API_TOKEN_MASKED = inspect.applied_config.get(KEY_API_TOKEN).value
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
                console.print(
                    NoteText(
                        "There is likely nothing wrong with the host server. "
                        "Possible reasons for failure:\n"
                        "• Invalid/expired/incorrect API token\n"
                        "• Incorrect host URL\n",
                    )
                )
                raise typer.Exit(1)
