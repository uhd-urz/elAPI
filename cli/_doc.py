"""
This script includes docstring for elabftw-get. The docstrings are mainly meant to be used with a CLI interface.
"""

__PARAMETERS__doc__ = {
    "endpoint": "Name of an endpoint. Valid endpoints are: apikeys, config, experiments, "
                "items, experiments_templates, items_types, event, events, team_tags, teams, "
                "todolist, unfinished_steps, users.",
    "unit_id": "ID for one of the preceding endpoints. If provided, only information associated with that "
               "ID will be returned. E.g., user ID, team ID, experiments ID.",
    "output": "Format style for printing output. Supported values are: **JSON**, **YAML**, **plaintext**. "
              "The values are case insensitive. The default format is `JSON`. "
              "When 'plaintext' is used, response will be sent to STDOUT in *original*, un-formatted, "
              "without syntax highlighting. This can be utilized if one wishes to pipe the output to "
              "some external formatting program like `less`. "
              "If an unsupported format value is provided then the output falls back to '-plaintext'."
}
