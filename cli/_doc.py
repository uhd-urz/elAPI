"""
This script includes docstring for elapi. The docstrings are mainly meant to be used with a CLI interface.
"""
from cli._format import BaseFormat
from src import APP_NAME

supported_highlighting_formats = ", ".join(f"**{_}**" for _ in BaseFormat.supported_formatter_names())

__PARAMETERS__doc__ = {
    "endpoint": "Name of an endpoint. Valid endpoints are: apikeys, config, experiments, info, "
                "items, experiments_templates, items_types, events, team_tags, teams, "
                "todolist, unfinished_steps, users, idps.",
    "unit_id_get": "ID for one of the preceding endpoints. If provided, only information associated with that "
                   "ID will be returned. E.g., user ID, team ID, experiments ID.",
    "unit_id_post": "ID for one of the preceding endpoints. If provided, `POST` request will be made against that "
                    "specific ID. E.g., events ID,.",
    "data": f"HTTP POST data. There are two ways to pass the data. 1. With `--data` or `-d` option followed "
            f"by the JSON content like with `curl`. E.g., "
            f"`{APP_NAME} post teams -d '{{\"name\": \"Alpha\"}}'`, 2. As regular options. E.g., "
            f"`{APP_NAME} post teams --name Alpha`.",
    "async": f"Beta: Make process asynchronous. This speeds up receiving data from eLabFTW server manyfold.",
    "invoice": f"Generate an invoice as well. Invoice will be saved in Markdown format.",
    "clean": "Remove cached data when finished. If `cleanup_after_finish` is 'true' in configuration file, "
             "_--cleanup_ is automatically applied.",
    "export": f"Export output to a location.\n"
              f"- If only _'--export'_ is passed, then it acts as a flag, and "
              f"`export_dir` value from configuration file is used. "
              f"It should be clear that `export_dir` in a configuration file only accepts a directory path.\n"
              f"- If a directory path is provided, "
              f"i.e., _'--export \<path/to/directory\>'_, then that path is used instead. "
              f"When the path is a directory, "
              f"the file name is auto-generated using the following scheme: *'\<FUNCTION\>_DATE_HHMMSS.EXT'*.\n"
              f"- If a file path is passed, i.e., _'--export <path/to/file.json>'_ "
              f"then data is simply exported to that file. "
              f"This allows custom file name scheme. The file extension however is ignored, "
              f"and always the format defined with _--output/-o_ option applies for the data format.",
    "output": f"Format style for the output. Supported values are: {supported_highlighting_formats}. "
              "The values are case insensitive. The default format is `JSON`. "
              "When 'txt' is used, the response will be sent in *original*, un-formatted (almost), "
              "without syntax highlighting. This can be utilized if one wishes to pipe the output "
              " to some external formatting program like `less`. "
              "If an unsupported format value is provided then the output falls back to 'txt'."
}
