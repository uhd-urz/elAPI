from ... import APP_NAME
from ...configuration import DEFAULT_EXPORT_DATA_FORMAT
from .formats import BaseFormat, _CSVFormat

supported_format_values = ", ".join(
    f"**{_.upper()}**"
    for _ in BaseFormat.supported_formatter_names(__package__)
)

__PARAMETERS__doc__ = {
    "invoice_export": "Export output to a location. Invoices are **always exported** by default.\n",
    "root_directory": "The root of the directory where store-info will create the billing directory structure, "
    "and save teams and owners information in `JSON`. store-info also sorts the JSON keys "
    "before saving.",
    "owners_data_path": "Source path for owners information `CSV` file. Internally referred to as the "
    "`'billing metadata'. --meta-source` is not required when `--teams-info-only` is passed, "
    "otherwise it is required.",
    "target_date": "ISO 8604 'YYYY-MM' for which 'YYYY/MM' directory to store.",
    "teams_info_only": "If passed, then only `teams-info` will be stored."
    "Both _--teams-info-only_ and _--owners-info-only_ cannot be passed.",
    "owners_info_only": "If passed, then only `owners-info` will be stored. "
    "Both _--teams-info-only_ and _--owners-info-only_ cannot be passed.",
    "data_format": f"Format style for the output. Supported values are: {supported_format_values}. "
                   f"{_CSVFormat.name.upper()} is **not** a supported format for this command as the "
                   f"output data structure is too complex for CSV. "
                   f"The values are case insensitive. The default format is `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`. "
                   "If an unsupported format value is provided then the output "
                   f"format falls back to `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`.",
    "export_details": f"- If _'--export'_ is passed without any following value, then it acts as a flag, and "
                      f"`export_dir` value from configuration file is used. "
                      f"It should be clear that `export_dir` in a configuration file only accepts a directory path.\n"
                      f"- If a directory path is provided as a value, "
                      f"i.e., _'--export \\<path/to/directory\\>'_, then that path is used instead. "
                      f"When the path is a directory, "
                      f"the file name is auto-generated using the following scheme: "
                      f"*'DATE_HHMMSS_\\<FUNCTION\\>.EXT'*.\n"
                      f"- If a file path is passed, i.e., _'--export <path/to/file.json>'_, "
                      f"then data is simply exported to that file. This allows custom file name scheme. "
                      f"If _--format/-F_ is absent, then {APP_NAME} can use the file extension as the data format. "
                      f"If _--format/-F_ is also present, then file extension is ignored, "
                      f"and --format value takes precedence.\n"

}
