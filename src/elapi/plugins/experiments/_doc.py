from ... import APP_NAME


__PARAMETERS__doc__ = {
    "experiment_id": "ID of an existing experiment. ID can be found on the URL of the experiment. "
                     "ID can also be 'Unique eLabID' that is visible on an experiment page.",
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
    "download_attachment_attachment_id": "ID of an existing attachment. Attachment IDs aren't shown on experiment "
                                         "pages. Attachment SHA can be seen by clicking \"More information\" "
                                         "of an attachment. First 6 digits (or more) of the attachment SHA256 "
                                         "hash can also be passed as an attachment ID.",

}
