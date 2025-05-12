from .formats import BaseFormat, PDFAFormat, ZIPAFormat
from ... import APP_NAME
from ...configuration import DEFAULT_EXPORT_DATA_FORMAT

supported_format_values = ", ".join(
    f"**{_.upper()}**"
    for _ in BaseFormat.supported_formatter_names(__package__)
)

__PARAMETERS__doc__ = {
    "experiment_id": "ID of an existing experiment. ID can be found on the URL of the experiment. "
                     "ID can also be 'Unique eLabID' that is visible on an experiment page. Note, "
                     "unique eLabIDs aren't persistent across different eLabFTW instances.",
    "append_content_text": "Raw text to append to an experiment body. Text must be UTF-8 encoded.",
    "append_content_path": "Path to a file whose content to append to an experiment. File content must be UTF-8 encoded. "
                           "If both --path and --text are passed, the expected outcome can be ambiguous, "
                           "so experiments plugin will shown an error and quit.",
    "append_markdown_to_html": "If this flag is passed, then experiments plugin will attempt to convert any markdown "
                               "text given with --text or --path to HTML. If given content isn't in markdown "
                               "then the text content is just wrapped with <p> tag. E.g., "
                               f"{APP_NAME} `--id <experiment ID> -M -t \"**New content.**\"`",
    "upload_attachment_path": "Path to the file to attach.",
    "upload_attachment_rename": "Rename file given with --path before attaching. "
                                "Rename will the rename the entire file name including its extension part.",
    "upload_attachment_comment": "Add text comment to a file.",
    "download_attachment_attachment_id": "ID of an existing attachment. Attachment IDs are not displayed on "
                                         "experiment pages. First 6 digits (or more) of the attachment SHA256 "
                                         "hash can also be passed as an attachment ID. "
                                         "Attachment SHA can be found by clicking the \"More information\" "
                                         "option of an attachment.",
    "data_format": f"Experiment output format. Supported values are: {supported_format_values}. "
                   f"{PDFAFormat.reference}, {ZIPAFormat.reference} are 'long-term storage' formats. "
                   f"The supported formats follow the _'Export'_ options available "
                   f"for an experiment on the browser GUI. As such, **only** JSON and YAML formats can be printed "
                   f"on the terminal. All other supported formats are exported to "
                   f"local storage by default (see _--export_ for more export options). "
                   f"The values are case insensitive. The default format is `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`. "
                   "If an unsupported format value is provided then the output format "
                   f"falls back to `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`.",
    "export_details": f"- If _'--export'_ is passed without any following value, then it acts as a flag, and "
                      f"`export_dir` value from configuration file is used. "
                      f"It should be clear that `export_dir` in a configuration file only accepts a directory path.\n"
                      f"- If a directory path is provided as a value, "
                      f"i.e., _'--export \\<path/to/directory\\>'_, then that path is used instead. "
                      f"When the path is a directory, "
                      r"the file name is auto-generated using the following scheme: *'DATE_HHMMSS_\<FUNCTION\>.EXT'*.\n"
                      f"- If a file path is passed, i.e., _'--export <path/to/file.json>'_, "
                      f"then data is simply exported to that file. This allows custom file name scheme. "
                      f"If _--format/-F_ is absent, then {APP_NAME} can use the file extension as the data format. "
                      f"If _--format/-F_ is also present, then file extension is ignored, "
                      f"and --format value takes precedence.\n",


}
