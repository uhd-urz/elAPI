import asyncio
import json
from pathlib import Path
from typing import Union

import typer
from rich.progress import track

from src import ProperPath, AsyncGETRequest, logger
from src.core_names import TMP_DIR


class Information:
    def __init__(self, unit_name: str, keep_session_open: bool = False):
        self.unit_name = unit_name
        self._session = AsyncGETRequest(keep_session_open=keep_session_open)

    @property
    def session(self) -> AsyncGETRequest:
        return self._session

    @session.setter
    def session(self, value):
        raise AttributeError("Session cannot be modified!")

    @property
    def DATA_FORMAT(self):
        return "json"

    async def json(self, unit_id: Union[str, int, None] = None, **kwargs) -> dict:
        response = await self.session(self.unit_name, unit_id)
        return response.json(**kwargs)


class FixedEndpoint:
    """An alias for Information class."""

    def __new__(cls, *args, **kwargs) -> Information:
        return Information(*args, **kwargs)


class RecurseInformation:
    def __init__(self, fixed_endpoint: Information):
        self.fixed_endpoint = fixed_endpoint
        self._cache_path = TMP_DIR

    async def _get_data(self) -> list[dict, ...]:
        recursive_unit_data_filename = (
            f"recursive_{self.fixed_endpoint.unit_name}_data"
            f".{self.fixed_endpoint.DATA_FORMAT}"
        )
        id_prefix = "userid" if self.fixed_endpoint.unit_name == "users" else "id"
        # to read ids from inside the response data
        # TODO: Not all unit names (endpoints) may not have their key name for id as 'id'

        # this will without a unit id create all_<information type>_data.json first
        unit_all_data = await self.fixed_endpoint.json(unit_id=None)
        self._cache_unit_data(
            unit_all_data,
            filename=f"all_{self.fixed_endpoint.unit_name}_data.{self.fixed_endpoint.DATA_FORMAT}",
        )

        tasks, recursive_unit_data = [], []
        for item in unit_all_data:
            tasks.append(self.fixed_endpoint.json(unit_id=item[id_prefix]))
        total_tasks: int = len(tasks)
        try:
            for task in track(
                asyncio.as_completed(tasks),
                description=f"Getting {self.fixed_endpoint.unit_name} data:",
                total=total_tasks,
            ):
                recursive_unit_data.append(await task)
        except asyncio.CancelledError:
            logger.warning(
                f"Request to '{self.__class__.__name__}' with "
                f"'{self.fixed_endpoint.unit_name}' is interrupted."
            )
            await self.fixed_endpoint.session.close()
            raise typer.Exit()

        await self.fixed_endpoint.session.close()
        self._cache_unit_data(
            recursive_unit_data, filename=recursive_unit_data_filename
        )
        return recursive_unit_data

    def _cache_unit_data(self, unit_data, filename: str = None) -> Path:
        """Writes unit data from converted JSON to a JSON file in pre-defined directory"""
        file_path = self._cache_path / filename
        with ProperPath(file_path).open("w", "utf-8") as file:
            file.write(json.dumps(unit_data, indent=2))
        return file_path

    def items(self) -> list[dict, ...]:
        return asyncio.run(self._get_data())
