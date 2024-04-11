from typing import Any

from ...styles.format import BaseFormat, JSONFormat


class JSONSortedFormat(JSONFormat, BaseFormat):
    def __call__(self, data: Any) -> str:
        import json

        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
