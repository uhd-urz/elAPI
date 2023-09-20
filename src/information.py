import json
from pathlib import Path
from typing import TypeAlias, Union, Optional

import typer
from rich.progress import track

from src import ProperPath, GETRequest, logger
from src.core_names import TMP_DIR

SPECIAL_RESPONSE: TypeAlias = tuple[Optional[int], Union[list[dict], dict]]


class Information:
    def __init__(self, unit_name: str, keep_session_open: bool = False):
        self.unit_name = unit_name
        self._session = GETRequest(keep_session_open=keep_session_open)

    @property
    def session(self) -> GETRequest:
        return self._session

    @session.setter
    def session(self, value):
        raise AttributeError("Session cannot be modified!")

    @property
    def DATA_FORMAT(self) -> str:
        return "json"

    def __call__(self, unit_id: Union[str, int, None] = None) -> dict:
        response = self.session(self.unit_name, unit_id)
        return response.json()


class FixedEndpoint:
    """An alias for Information class."""

    def __new__(cls, *args, **kwargs) -> Information:
        return Information(*args, **kwargs)


class RecurseInformation:
    def __init__(self, fixed_endpoint: Information):
        self.fixed_endpoint = fixed_endpoint
        self._cache_path = TMP_DIR

    def _get_data(self) -> list[dict, ...]:
        recursive_unit_data_filename = (f"recursive_{self.fixed_endpoint.unit_name}_data"
                                        f".{self.fixed_endpoint.DATA_FORMAT}")
        id_prefix = "userid" if self.fixed_endpoint.unit_name == "users" else "id"
        # to read ids from inside the response data
        # TODO: Not all unit names (endpoints) may not have their key name for id as 'id'

        # this will without a unit id create all_<information type>_data.json first
        unit_all_data = self.fixed_endpoint(unit_id="")
        self._cache_unit_data(unit_all_data,
                              filename=f"all_{self.fixed_endpoint.unit_name}_data.{self.fixed_endpoint.DATA_FORMAT}")
        recursive_unit_data = []
        try:
            for item in track(unit_all_data, description=f"Getting {self.fixed_endpoint.unit_name} data:"):
                recursive_unit_data.append(self.fixed_endpoint(unit_id=item[id_prefix]))
        except KeyboardInterrupt:
            logger.warning(f"Request to '{self.__class__.__name__}' with "
                           f"'{self.fixed_endpoint.unit_name}' is interrupted.")
            self.fixed_endpoint.session.close()
            raise typer.Exit()

        self.fixed_endpoint.session.close()
        self._cache_unit_data(recursive_unit_data, filename=recursive_unit_data_filename)
        return recursive_unit_data

    def _cache_unit_data(self, unit_data, filename: str = None) -> Path:
        """Writes unit data from converted JSON to a JSON file in pre-defined directory"""
        file_path = self._cache_path / filename
        with ProperPath(file_path).open("w", "utf-8") as file:
            file.write(json.dumps(unit_data, indent=2))
        return file_path

    def __call__(self) -> list[dict, ...]:
        return self._get_data()
