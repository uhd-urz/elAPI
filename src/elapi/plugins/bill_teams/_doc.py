from .formats import BaseFormat, _CSVFormat
from .specification import CLI_DATE_VALID_FORMAT, BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB, \
    BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB, REGISTRY_FILE_NAME
from ... import APP_NAME
from ..._names import LOG_FILE_NAME
from ...configuration import DEFAULT_EXPORT_DATA_FORMAT

supported_format_values = ", ".join(
    f"**{_.upper()}**"
    for _ in BaseFormat.supported_formatter_names(__package__)
)

__PARAMETERS__doc__ = {
    "invoice_export": "Export output to a location. Invoices are **always exported** by default.\n",
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
                      f"and --format value takes precedence.\n",
    "start_date": f"Billing start year and month. The value must be ISO 8601 compliant, and "
                  f"in the following format only: **{CLI_DATE_VALID_FORMAT}**. "
                  f"If no --start-date is passed, then month that is 6 months in the past "
                  f"from --end-date is assumed.",
    "end_date": f"Billing end year and month. The value must be ISO 8601 compliant, and "
                f"in the following format only: **{CLI_DATE_VALID_FORMAT}**. "
                f"If no --end-date is passed, then the month that is 6 months in the future "
                f"from --start-date is assumed. --end-date is always inclusive as months start from 1 (this is "
                f"similar to 1-based indexing). If neither --end-date nor --start-date is passed, then "
                f"the month before the current month is assumed for --end-date.",
    "registry_team_id": "Target team ID. If not team ID is passed, then all team IDs are targeted.",
    "do_not_print_missing_in_teams_info_log": f"A warning log is shown if team is found in "
                                              f"'{BILLING_INFO_OUTPUT_OWNERS_INFO_FILE_NAME_STUB}' but not in "
                                              f"'{BILLING_INFO_OUTPUT_TEAMS_INFO_FILE_NAME_STUB}'. However, "
                                              f"this log message can clutter the terminal if the "
                                              f"situation is expected. Passing "
                                              f"_--do-not-print-missing-in-teams-info-log_ will only store those logs "
                                              f"in {LOG_FILE_NAME} file. A single warning message will still be "
                                              f"shown to at least inform the user. **Note:** The log messages are "
                                              f"only generated when {REGISTRY_FILE_NAME} file is first populated "
                                              f"(i.e., when the file doesn't exist, and is being created "
                                              f"for the first time).",
    "include_force": f"Force include team to registry. If a team has been billed already, "
                     f"then team cannot be **re-included** to registry without _--force_.",
    "ot_datum": "Year and month for the 'Datum' column. The value must be ISO 8601 compliant, and "
                f"in the following format only: **{CLI_DATE_VALID_FORMAT}**. Always, the first day of "
                f"the month is assumed. When no _--datum_ is passed, the current month is assumed.",
    "ot_include_monthly_bill": "By default, monthly bill columns (i.e., 'Gesamt' columns) are not filled in, "
                               "leaving them to Excel. They can be filled in by "
                               "passing _--include-monthly-bill_/_--imb_.",
    "ot_dry_run": "When _--dry-run_ is passed, generate-table will defer from asking registry "
                  "to make any updates (e.g., incrementing billing counter). This can be useful for "
                  "testing.",
    "ot_ignore_exempt": "generate-table will listen to the registry files for what teams "
                        "to include and what to exempt. _--ignore-exempt_ can be passed to ignore "
                        "the include/exempt status assigned to a team in the registry so that all teams "
                        "are included into the output table regardless of their include/exempt status "
                        "and billing counter. _--dry-run_ is always assumed when _--ignore-exempt_. "
                        "This can be useful for testing.",
    "ot_include_team_id": "By default, team IDs are not included. A new column with team IDs will be included "
                          "with _--include-team-id/--iti_. This can be useful for debugging.",
}
