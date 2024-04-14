from ...configuration import DEFAULT_EXPORT_DATA_FORMAT

_UNIQUE_SUPPORTED_FORMATS = ["json", "yaml", "txt"]
supported_format_values = ", ".join(
    f"**{_.upper()}**" for _ in _UNIQUE_SUPPORTED_FORMATS
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
                   f"CSV is **not** a supported format for this command as the "
                   f"output data structure is too complex for naive CSV. "
                   f"The values are case insensitive. The default format is `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`. "
                   "When 'txt' is used, the response will be sent in *original*, un-formatted (almost), "
                   "without syntax highlighting. This can be utilized if one wishes to pipe the output "
                   " to some external formatting program like `less`. "
                   "If an unsupported format value is provided then the output "
                   f"format falls back to `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`.",
}
