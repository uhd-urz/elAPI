import asyncio
from json import JSONDecodeError
from typing import Awaitable, Optional

import httpx
from httpx import Response
from rich.progress import Progress
from rich.text import Text

from ...api import GlobalSharedSession
from ...core_validators import Exit
from ...loggers import Logger
from ...styles import stdout_console

logger = Logger()
_RETRY_TRIGGER_ERRORS = (
    httpx.TimeoutException,
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    TimeoutError,
)


class Information:
    __slots__ = "endpoint_name"

    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name

    def items(self) -> list[dict]:
        from ...api import GETRequest

        session = GETRequest()
        try:
            response = session(endpoint_name=self.endpoint_name, endpoint_id=None)
        except _RETRY_TRIGGER_ERRORS as e:
            raise InterruptedError from e
        except KeyboardInterrupt as e:
            raise Exit(1) from e
        else:
            if response.is_success:
                return response.json()
            logger.error(
                f"Request for '{self.endpoint_name}' information was not successful! "
                f"Returned response was: '{response.text}'"
            )
            raise RuntimeError
        finally:
            session.close()


class RecursiveInformation:
    __slots__ = "endpoint_name", "endpoint_id_key_name"

    def __init__(self, endpoint_name: str, endpoint_id_key_name: str):
        self.endpoint_name = endpoint_name
        self.endpoint_id_key_name = endpoint_id_key_name

    @staticmethod
    async def cleanup_remaining(
        event_loop: asyncio.AbstractEventLoop, endpoint
    ) -> None:
        await endpoint.aclose()
        # Must be closed before cancelling asyncio tasks or stopping the event loop
        event_loop.set_exception_handler(lambda loop, context: ...)
        # "lambda loop, context: ..." suppresses asyncio error emission:
        # https://docs.python.org/3/library/asyncio-dev.html#detect-never-retrieved-exceptions
        for task in asyncio.all_tasks(event_loop):
            task.cancel()

    async def items(
        self,
        description: Optional[str] = None,
        log_keyboard_interrupt_message: bool = True,
        *,
        transient: bool = True,
        **kwargs,
    ):
        from ...api.endpoint import FixedAsyncEndpoint, RecursiveGETEndpoint

        event_loop = asyncio.get_running_loop()
        endpoint = FixedAsyncEndpoint(endpoint_name=self.endpoint_name)
        endpoint_information = Information(self.endpoint_name).items()
        description = description or f"Getting {self.endpoint_name} data:"
        try:
            recursive_endpoint = RecursiveGETEndpoint(
                endpoint_information,
                self.endpoint_id_key_name,
                target_endpoint=endpoint,
            )
            tasks: list[Awaitable[Response]] = [
                item for item in recursive_endpoint.endpoints()
            ]
            recursive_information: list = []
            with Progress(transient=transient, **kwargs) as progress:
                for task in progress.track(
                    asyncio.as_completed(tasks),
                    total=len(tasks),
                    description=description,
                ):
                    response = await task
                    try:
                        recursive_information.append(response.json())
                    except JSONDecodeError as e:
                        stdout_console.print()  # Print a new line to not overlap with progress bar
                        logger.warning(
                            f"Request for '{self.endpoint_name}' data was received by the server but "
                            f"request was not successful. Response status: {response.status_code}. "
                            f"Exception details: '{e!r}'. "
                            f"Response: '{response.text}'"
                        )
                        await self.cleanup_remaining(event_loop, endpoint)
                        raise InterruptedError from e
        except _RETRY_TRIGGER_ERRORS as error:
            stdout_console.print()
            logger.warning(
                f"Retrieving {self.endpoint_name} data was interrupted due to a network error. "
                f"Exception details: '{error!r}'"
            )
            await self.cleanup_remaining(event_loop, endpoint)
            raise InterruptedError from error
        except (KeyboardInterrupt, asyncio.CancelledError) as e:
            if log_keyboard_interrupt_message is True:
                curr_percentage: Text = progress.columns[2]._renderable_cache[0][1]
                curr_percentage: str = curr_percentage.plain.strip()
                logger.error(
                    f"'{KeyboardInterrupt.__name__}' (or similar) aborted "
                    f"progress at {curr_percentage}."
                )
            await self.cleanup_remaining(event_loop, endpoint)
            if GlobalSharedSession._instance is not None:
                GlobalSharedSession().close()
            raise Exit(1) from e
        else:
            await endpoint.aclose()
            return recursive_information
