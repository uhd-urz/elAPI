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


def remove_csv_formatter_support():
    from ...styles.format import BaseFormat, CSVFormat

    try:
        del BaseFormat.supported_formatters()[CSVFormat.pattern()]
        del BaseFormat.supported_formatter_names()[
            BaseFormat.supported_formatter_names().index(CSVFormat.name)
        ]
        # noinspection PyProtectedMember
        del BaseFormat._conventions[BaseFormat._conventions.index(CSVFormat.convention)]

    except KeyError:
        ...
