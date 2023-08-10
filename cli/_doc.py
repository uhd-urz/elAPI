"""
This script includes docstring for elabftw-get. The docstrings are mainly meant to be used with a CLI interface.
"""

__PARAMETERS__doc__ = {
    "endpoint": f"Name of an endpoint. Valid endpoints are: apikeys, config, experiments, "
                f"items, experiments_templates, items_types, event, events, team_tags, teams, "
                f"todolist, unfinished_steps, users.",
    "unit_id": f"ID for one of the preceding endpoints. If provided, only information associated with that "
               f"ID will be returned. E.g., user ID, team ID, experiments ID.",
    "plaintext": f"When --plaintext is provided, response will be sent to STDOUT un-formatted (without syntax "
                 f"highlighting).This can be utilized if one wishes to use external formatting."
}
