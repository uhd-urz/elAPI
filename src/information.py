import json
from shutil import copy2
from typing import Union
from src._custom_types import ListWithID
import elabapi_python
from src.defaults import api_client
from src._config_handler import DATA_DOWNLOAD_DIR
from src._app_data_handler import RESPONSE_DATA_DIR
from pathlib import Path
import ast


class Information:
    __INFORMATION_TYPE = {
        "users": elabapi_python.UsersApi,
        "teams": elabapi_python.TeamsApi,
        "experiments": elabapi_python.ExperimentsApi
    }

    def __init__(self, information_type: str, unit_data_export_dir: Union[str, Path] = None):
        self.information_type = information_type
        self.unit = Information.__INFORMATION_TYPE[information_type](api_client)
        self.unit_data_export_dir = unit_data_export_dir if unit_data_export_dir else DATA_DOWNLOAD_DIR if (
            DATA_DOWNLOAD_DIR) else Path.home() / 'Downloads'

    def _read_unit(self, unit_id: int = None):
        if self.information_type == "users":
            return self.unit.read_users() if not unit_id else self.unit.read_user(id=unit_id)
        elif self.information_type == "teams":
            return self.unit.read_teams() if not unit_id else self.unit.read_team(id=unit_id)
        elif self.information_type == "experiments":
            return self.unit.read_experiments() if not unit_id else self.unit.read_experiment(id=unit_id)

    def get_unit_data(self, unit_id: int = None):
        """Fetches the current unit list from direct API response without any changing the format."""
        return ListWithID([unit_id, self._read_unit()]) if not unit_id else ListWithID(
            [unit_id, self._read_unit(unit_id=unit_id)])

    @staticmethod
    def file_already_exists(directory: Union[Path, str], filename: Union[str, Path]):
        if (Path(directory) / filename).exists():
            return directory / filename

    def get_extensive_unit_data(self, unit_id: int = None, filename: Union[Path, str] = None,
                                ignore_existing_filename: bool = True) -> Path:
        filename = filename if filename else f"extensive_{self.information_type}_data.json"
        id_prefix = "userid" if self.information_type == "users" else "id"  # This is subject to change

        if not ignore_existing_filename:
            return self.file_already_exists(RESPONSE_DATA_DIR, filename)

        # this will without a unit id create all_<information type>_data.json first
        all_unit_data_path = self._cache_unit_data(self.get_unit_data(unit_id))

        with open(all_unit_data_path, "r", encoding="utf-8") as file:
            structured = json.loads(file.read())

        if not unit_id:
            unit_data_list = []
            for item in structured:
                unit_id, raw_data = self.get_unit_data(unit_id=item[id_prefix])
                unit_data_list.append(raw_data)

            return self._cache_unit_data(unit_data=unit_data_list, filename=filename)

        return self._cache_unit_data(self.get_unit_data(unit_id=structured[id_prefix]))

    def _cache_unit_data(self, unit_data: Union[ListWithID, dict, str, json], filename: str = None,
                         ignore_existing_filename: bool = True) -> Path:
        """Writes unit data from converted JSON to a JSON file in pre-defined directory"""
        data_path = RESPONSE_DATA_DIR
        unit_id, raw_data = unit_data if isinstance(unit_data, ListWithID) else (None, unit_data)

        # First we are saving it in a temporary directory: /var/tmp/elabftw-get
        filename = filename if filename else f"all_{self.information_type}.json" if unit_id is None \
            else f"{self.information_type}_{unit_id}.json"

        if not ignore_existing_filename:
            return self.file_already_exists(data_path, filename)

        with open(data_path / filename, "w", encoding="utf-8") as file:
            file.write(self._convert_to_json(raw_data))

        return data_path / filename

    def export_unit(self, export_path: Union[str, Path, bool] = None, suppress_message: bool = False,
                    **kwargs) -> Path:

        filepath = self._cache_unit_data(**kwargs)
        if export_path == 'cache':
            return filepath

        export_path = export_path if export_path else self.unit_data_export_dir
        copy2(filepath, export_path)

        if not suppress_message:
            print(f"{self.information_type} data successfully exported to: {self.unit_data_export_dir}/{filepath.name}")
        return self.unit_data_export_dir / filepath.name

    @staticmethod
    def _convert_to_dict(raw_data: Union[str, list]):
        """Converts unit data to Python dictionary, so it can be later parsed with ease"""
        try:
            return [ast.literal_eval(str(_)) for _ in raw_data]
        except TypeError:
            return ast.literal_eval(str(raw_data))

    def _convert_to_json(self, raw_data: Union[str, list]):
        """Converts dictionary to JSON"""
        return json.dumps(self._convert_to_dict(raw_data))


if __name__ == '__main__':
    u = Information(information_type="users")
    # data = u.get_unit_data()
    # u.export_unit(data)
    # data = u.get_extensive_unit_data()
    # u.export_unit(data)
    t = Information(information_type="teams")
    # print(t.get_extensive_unit_data(unit_id=1))
