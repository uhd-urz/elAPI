import json
from shutil import copy2
from typing import Union
from src._config_handler import DATA_DOWNLOAD_DIR
from src._app_data_handler import RESPONSE_DATA_DIR
from cli.elabftw_get import elabftw_response
from pathlib import Path


class Information:

    def __init__(self, unit_name: str, unit_data_export_dir: Union[str, Path] = None):
        self.unit_name = unit_name
        self.unit_data_export_dir = unit_data_export_dir if unit_data_export_dir else DATA_DOWNLOAD_DIR

    def get_unit_data(self, unit_id: Union[None, int] = None) -> tuple[Union[None, int], Union[list[dict], dict]]:
        """Fetches the current unit list from direct API response without changing the format."""
        response = elabftw_response(endpoint=self.unit_name, unit_id=unit_id).json()
        return unit_id, response

    @staticmethod
    def file_already_exists(directory: Path, filename: Union[str, Path]):
        if (directory / filename).exists():
            return directory / filename

    def get_extensive_unit_data_path(self, unit_id: Union[None, int] = None, filename: Union[Path, str] = None,
                                     ignore_existing_filename: bool = True) -> Path:
        filename = filename if filename else f"extensive_{self.unit_name}_data.json"
        id_prefix = "userid" if self.unit_name == "users" else "id"  # to read ids from inside the response data
        # TODO: Not all unit names (endpoints) may not have their key name for id as 'id'

        if not ignore_existing_filename:
            return self.file_already_exists(RESPONSE_DATA_DIR, filename)

        # this will without a unit id create all_<information type>_data.json first
        all_unit_data_path = self._cache_unit_data(self.get_unit_data(unit_id=unit_id))

        with open(all_unit_data_path, "r", encoding="utf-8") as file:
            structured = json.loads(file.read())

        if not unit_id:
            unit_data_list = []
            for item in structured:
                unit_id, raw_data = self.get_unit_data(unit_id=item[id_prefix])
                unit_data_list.append(raw_data)

            return self._cache_unit_data(unit_data=(None, unit_data_list), filename=filename)

        return self._cache_unit_data(unit_data=self.get_unit_data(unit_id=structured[id_prefix]))

    def _cache_unit_data(self, unit_data: tuple[Union[None, int], Union[list[dict], dict]], filename: str = None,
                         ignore_existing_filename: bool = True) -> Path:
        """Writes unit data from converted JSON to a JSON file in pre-defined directory"""
        FILE_EXT = 'json'
        data_path = RESPONSE_DATA_DIR
        unit_id, raw_data = unit_data

        # First we are saving it in a temporary directory: /var/tmp/elabftw-get
        filename = filename if filename else f"all_{self.unit_name}.{FILE_EXT}" if not unit_id \
            else f"{self.unit_name}_{unit_id}.{FILE_EXT}"

        if not ignore_existing_filename:
            return self.file_already_exists(data_path, filename)

        with open(data_path / filename, "w", encoding="utf-8") as file:
            file.write(self._convert_to_json(raw_data))

        return data_path / filename

    def export_data(self, data: tuple[Union[None, int], Union[list[dict], dict]],
                    export_path: Union[Path, str, None] = None,
                    suppress_message: bool = False, **kwargs) -> Path:

        filepath = self._cache_unit_data(unit_data=data, **kwargs)
        # kwargs can be used to modify file name or ignore existing
        if export_path == 'cache':
            return filepath

        export_path = export_path if export_path else self.unit_data_export_dir
        copy2(filepath, export_path)

        if not suppress_message:
            print(f"{self.unit_name} data successfully exported to: {self.unit_data_export_dir}/{filepath.name}")
        return self.unit_data_export_dir / filepath.name

    @staticmethod
    def _convert_to_json(raw_data: Union[list, dict]) -> str:
        """Converts dictionary to JSON"""
        return json.dumps(raw_data)
