import asyncio
from typing import Awaitable

import httpx
from httpx import Response

from ...loggers import Logger

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

    def items(self) -> list[dict, ...]:
        from ...api import GETRequest

        session = GETRequest()
        try:
            response = session(endpoint_name=self.endpoint_name, endpoint_id=None)
        except _RETRY_TRIGGER_ERRORS:
            session.close()
            raise InterruptedError
        except KeyboardInterrupt:
            session.close()
            raise SystemExit(1)
        else:
            if response.is_success:
                return response.json()
            logger.error(
                f"Request for '{self.endpoint_name}' information was not successful! "
                f"Returned response was: '{response.text}'"
            )
            raise RuntimeError


class RecursiveInformation:
    __slots__ = "endpoint_name", "endpoint_id_key_name", "verbose"

    def __init__(
        self, endpoint_name: str, endpoint_id_key_name: str, verbose: bool = True
    ):
        self.endpoint_name = endpoint_name
        self.endpoint_id_key_name = endpoint_id_key_name
        self.verbose = verbose

    async def items(self):
        from ...endpoint import FixedAsyncEndpoint, RecursiveGETEndpoint
        from rich.progress import track

        event_loop = asyncio.get_running_loop()
        _endpoint = FixedAsyncEndpoint(endpoint_name=self.endpoint_name)
        endpoint_information = Information(self.endpoint_name).items()
        try:
            recursive_endpoint = RecursiveGETEndpoint(
                endpoint_information,
                self.endpoint_id_key_name,
                target_endpoint=_endpoint,
            )
            tasks: list[Awaitable[Response]] = [
                item for item in recursive_endpoint.endpoints()
            ]
            recursive_information: list = []
            for task in track(
                asyncio.as_completed(tasks),
                total=len(tasks),
                description=f"Getting {self.endpoint_name} data:",
                transient=True,
                disable=not self.verbose,
            ):
                recursive_information.append((await task).json())
        except _RETRY_TRIGGER_ERRORS as error:
            logger.warning(
                f"Retrieving {self.endpoint_name} data was interrupted due to a network error. "
                f"Exception details: '{error!r}'"
            )
            event_loop.set_exception_handler(lambda loop, context: ...)
            # "lambda loop, context: ..." suppresses asyncio error emission:
            # https://docs.python.org/3/library/asyncio-dev.html#detect-never-retrieved-exceptions
            await _endpoint.close()
            if event_loop.is_running():
                event_loop.stop()  # Will raise RuntimeError
            raise InterruptedError  # This will likely never be reached,
            # since this entire exception block will only trigger while event loop is still running
        except (KeyboardInterrupt, asyncio.CancelledError):
            await _endpoint.close()
            event_loop.stop()
            raise SystemExit(1)
        else:
            await _endpoint.close()
            return recursive_information
