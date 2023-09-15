import json
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import Union, ClassVar

from src import ProperPath, elabftw_fetch
from src._config_handler import DOWNLOAD_DIR
from src.core_names import TMP_DIR


@dataclass(slots=True)
class Information:
    unit_name: str
    unit_data_export_dir: Union[str, Path] = DOWNLOAD_DIR
    DATA_FILE_EXT: ClassVar[str] = "json"

    def get_unit_data(self, unit_id: Union[None, int] = None) -> tuple[Union[None, int], Union[list[dict], dict]]:
        """Fetches the current unit list from direct API response without changing the format."""
        response = elabftw_fetch(endpoint=self.unit_name, unit_id=unit_id).json()
        return unit_id, response

    def get_extensive_unit_data_path(self, unit_id: Union[None, int] = None, filename: Union[Path, str] = None,
                                     ignore_existing_filename: bool = True) -> Path:
        filename = filename if filename else f"extensive_{self.unit_name}_data.{Information.DATA_FILE_EXT}"
        id_prefix = "userid" if self.unit_name == "users" else "id"  # to read ids from inside the response data
        # TODO: Not all unit names (endpoints) may not have their key name for id as 'id'

        if not ignore_existing_filename:
            return ProperPath(TMP_DIR / filename).exists()

        # this will without a unit id create all_<information type>_data.json first
        all_unit_data_path = self._cache_unit_data(self.get_unit_data(unit_id=unit_id))

        with ProperPath(all_unit_data_path).open(mode="r", encoding="utf-8") as file:
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
        # FILE_EXT = 'json'
        data_path = TMP_DIR
        unit_id, raw_data = unit_data

        # First we are saving it in a temporary directory: /var/tmp/elapi
        filename = filename if filename else f"all_{self.unit_name}.{Information.DATA_FILE_EXT}" if not unit_id \
            else f"{self.unit_name}_{unit_id}.{Information.DATA_FILE_EXT}"

        if not ignore_existing_filename:
            return ProperPath(data_path / filename).exists()

        with ProperPath(data_path / filename).open("w", "utf-8") as file:
            file.write(json.dumps(raw_data))

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
