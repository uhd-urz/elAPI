"""
This script includes docstring for elapi. The docstrings are mainly meant to be used with a CLI interface.
"""
from cli._highlight_syntax import Highlight
from src import APP_NAME
from src.core_names import FALLBACK_DOWNLOAD_DIR

supported_highlighting_formats = ", ".join(f"**{_}**" for _ in Highlight.SUPPORTED_FORMAT.keys())

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
    "clean": "Remove cached data when finished. If `cleanup_after_finish` is 'true' in configuration file, "
             "_--cleanup_ is automatically applied.",
    "export": f"Beta: Export output to `download_dir` defined in configuration file. "
              f"If `download_dir` is not defined, then _--export_ falls back to `{FALLBACK_DOWNLOAD_DIR}`."
              f"_--export_ doesn't support a new path as argument.",
    "output": f"Format style for printing output. Supported values are: {supported_highlighting_formats}. "
              "The values are case insensitive. The default format is `JSON`. "
              "When 'txt' is used, response will be sent to STDOUT in *original*, un-formatted, "
              "without syntax highlighting. This can be utilized if one wishes to pipe the output to "
              "some external formatting program like `less`. "
              "If an unsupported format value is provided then the output falls back to 'txt'."
}
