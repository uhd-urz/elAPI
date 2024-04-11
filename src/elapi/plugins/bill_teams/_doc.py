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
}
