from typing import Any

from ...styles.formats import BaseFormat, JSONFormat, CSVFormat as _CSVFormat


class JSONSortedFormat(JSONFormat, BaseFormat):
    package_identifier = __package__

    def __call__(self, data: Any) -> str:
        import json

        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )


class DisabledCSVFormat(_CSVFormat, BaseFormat):
    name = None
    package_identifier = __package__

    def __call__(self, data: Any):
        raise NotImplementedError
