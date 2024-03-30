import asyncio
from json import JSONDecodeError
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
        except _RETRY_TRIGGER_ERRORS as e:
            raise InterruptedError from e
        except KeyboardInterrupt as e:
            raise SystemExit(1) from e
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
            raise InterruptedError from error  # This will likely never be reached,
            # since this entire exception block will only trigger while event loop is still running
            # but event loop is already closed in finally block which raises RuntimeError.
        except JSONDecodeError as e:
            logger.warning(
                f"Request for '{self.endpoint_name}' data was received by the server but "
                f"request was not successful."
            )
            raise InterruptedError from e
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise SystemExit(1)
        else:
            return recursive_information
        finally:
            event_loop.set_exception_handler(lambda loop, context: ...)
            # "lambda loop, context: ..." suppresses asyncio error emission:
            # https://docs.python.org/3/library/asyncio-dev.html#detect-never-retrieved-exceptions
            await _endpoint.close()  # Must be closed before cancelling asyncio tasks.
            for task in asyncio.all_tasks(event_loop):
                task.cancel()
            if event_loop.is_running():
                event_loop.stop()  # Will raise RuntimeError
