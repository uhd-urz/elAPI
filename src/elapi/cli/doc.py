"""
This script includes docstring for elapi. The docstrings are mainly meant to be used with a CLI interface.
"""
from .._names import CONFIG_FILE_NAME
from ..configuration import APP_NAME, DEFAULT_EXPORT_DATA_FORMAT, EXPORT_DIR
from ..styles import BaseFormat

supported_highlighting_formats = ", ".join(
    f"**{_.upper()}**" for _ in BaseFormat.supported_formatter_names()
)

__PARAMETERS__doc__ = {
    "endpoint_name": "Name of an endpoint. Valid endpoints are: apikeys, config, experiments, info, "
                     "items, experiments_templates, items_types, events, team_tags, teams, "
                     "todolist, unfinished_steps, users, idps.",
    "endpoint_id_get": "ID for one of the preceding endpoints. If provided, only information associated with that "
                     "ID will be returned. E.g., user ID, team ID, experiments ID.",
    "endpoint_id_post": "ID for a preceding endpoint. If provided, `POST` request will be made against that "
    "specific ID. E.g., events ID,.",
    "endpoint_id_patch": "ID for one of the preceding endpoints. If provided, `PATCH` request will be made "
                         "against that specific ID. E.g., events ID.",
    "endpoint_id_delete": "ID for one of the preceding endpoints. If provided, `DELETE` request will be made "
                         "against that specific ID. E.g., experiments ID.",
    "sub_endpoint_name": "Name of a sub-endpoint. Not all endpoints have sub-endpoints. "
                         "'uploads' is the sub-endpoint name of the API URL "
                         "_'https://demo.elabftw.net/api/v2/experiments/1/`uploads`/'_. "
                         "Consult the documentation for a list of available sub-endpoints of an endpoint.",
    "sub_endpoint_id": "ID for a preceding sub-endpoint. "
                        "'10' is the sub-endpoint ID of sub-endpoint 'uploads' of the API URL "
                        "_'https://demo.elabftw.net/api/v2/experiments/1/uploads/`10`/'_.",
    "query": "HTTP query to pass to API URL.\n"
             "- The value (parameters) for --query should be in **JSON** format. "
             f"E.g., `{APP_NAME} get experiments <experiment ID> --query '{{\"format\": \"csv\"}}'` "
             f"will make a `GET` request to "
             f"_'https://demo.elabftw.net/api/v2/experiments/\<experiment ID\>/?format=csv'_ "
             f"which in response will send back the experiment with \<experiment ID\> in CSV format.\n"
             f"- --query can be powerful. It can be used to make requests for arbitrary data formats "
             f"which can conflict with how --format/-F works. Hence, --format is disabled (i.e., it takes no effect) "
             f"when --query is passed.",
    # "data": f"HTTP POST data. There are two ways to pass the data. 1. With `--data` or `-d` option followed "
    #         f"by the JSON content like with `curl`. E.g., "
    #         f"`{APP_NAME} post teams -d '{{\"name\": \"Alpha\"}}'`, 2. As regular options. E.g., "
    #         f"`{APP_NAME} post teams --name Alpha`.",
    "data": f"HTTP POST data. This works similar to how data is passed to `curl`. E.g., "
            f"`{APP_NAME} post teams -d '{{\"name\": \"Alpha\"}}'`,",
    "file_post": "Send a file with a request. The value for --file should be in **JSON** format. The value must follow "
                 "one of the following structures: `'{\"file\": \"<file path>\"}'`, "
                 "`'{\"file\": \"<file path>\", \"comment\": \"<file comment>\"}'`, "
                 "`'{\"file\": [\"<file new name>\", \"<file path>\"]}'`, or "
                 "`'{\"file\": [\"<file new name>\", \"<file path>\"], \"comment\": \"<file comment>\"}'`.",
    "data_patch": f"Modified data to be sent as HTTP PATCH data. This works similar to how data is passed to `curl`. "
                  f'E.g., `{APP_NAME} patch teams --id <team id> -d \'{{"name": "New team name"}}\'`,',
    "get_loc": "When _--get-loc_ is passed, if the request is successful, instead of printing the success message, "
               f"{APP_NAME} returns the ID and the URL (separated by comma) of the newly created resource that can "
               f"be used to just modify or do automation with the resource later on. The ID and the URL can be "
               f"captured and saved to variables with `cut`. E.g., We can create a new experiment, "
               f"and get its ID with: `{APP_NAME} post experiments | cut -d \",\" -f 1`",
    "export": "Export output to a location.\n",
    "export_details": f"- If _'--export'_ is passed without any following value, then it acts as a flag, and "
              f"`export_dir` value from configuration file is used. "
              f"It should be clear that `export_dir` in a configuration file only accepts a directory path.\n"
              f"- If a directory path is provided as a value, "
              f"i.e., _'--export \<path/to/directory\>'_, then that path is used instead. "
              f"When the path is a directory, "
              f"the file name is auto-generated using the following scheme: *'DATE_HHMMSS_\<FUNCTION\>.EXT'*. "
              f"File extension (EXT) cannot always be inferred if response data is in binary which can be the case if "
              f"**--query is used** to define data format. In which case, --export will save the data to a "
              f"file with `.bin` extension. To avoid this, a proper file path with correct extension "
              f"should be passed to --export.\n"
              f"- If a file path is passed, i.e., _'--export <path/to/file.json>'_, "
              f"then data is simply exported to that file. This allows custom file name scheme. "
              f"If _--format/-F_ is absent, then {APP_NAME} can use the file extension as the data format. "
              f"If _--format/-F_ is also present, then file extension is ignored, "
              f"and --format value takes precedence.\n",
    "export_overwrite": f"If given --export/-e path is a file, but it already **exists**, "
                        f"{APP_NAME} will not overwrite the file by default, and will instead use the "
                        f"fallback location. _--overwrite_ needs to be passed if {APP_NAME} should overwrite "
                        f"an existing file when exporting.",
    "data_format": f"Format style for the output. Supported values are: {supported_highlighting_formats}. "
              f"The values are case insensitive. The default format is `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`. "
              "When 'txt' is used, the response will be sent in *original*, un-formatted (almost), "
              "without syntax highlighting. This can be utilized if one wishes to pipe the output "
              " to some external formatting program like `less`. "
              "If an unsupported format value is provided then the output format "
              f"falls back to `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`.",
    "verify": "SSL certificates are verified for HTTPS requests by default. Passing _'--verify False'_ will "
              "disable the verification. This can be useful during local development. You can also pass a "
              "path to SSL certificate (a.k.a CA bundle) file to --verify.",
    "timeout": f"Maximum number of seconds {APP_NAME} will wait for response before giving up. "
               f"Default timeout is **5** seconds.",
    "headers": f"{APP_NAME} decides the appropriate headers in most cases. --headers will let you overwrite "
               f"the default headers sent. The value for --headers should be in **JSON** format. E.g., "
               f"`{APP_NAME} get info --headers '{{\"Accept\": \"application/json\", \"User-Agent\": "
               f"\"My custom agent 1.0\"}}'`.",
    "no_keys": "Do not show the names of configuration keywords.",
    "init_host": 'The host URL of your eLabFTW instance. It will look like \"https://demo.elabftw.net/api/v2\".',
    "init_api_token": 'API token (or API key) of your eLabFTW instance. You can generate it from eLabFTW "User Panel". '
                      'Make sure your API key has proper permission for your future tasks.',
    "init_export_dir": f"Preferred export directory. If '--export-dir' isn't passed, {EXPORT_DIR} will be "
                        "set as the export directory.",
    "cli_startup": f"⚡️Force override detected configuration from '{CONFIG_FILE_NAME}'. "
                     "The value should be in **JSON** format. This option can only be passed "
                     "**before** passing any other argument/option/command. E.g., "
                     '`elapi --OC \'{"timeout": "10", "verify_ssl": "false"}\' get info -F yml`. '
                   'You can use tools like [yq](https://mikefarah.gitbook.io/yq) and '
                   '[jq](https://jqlang.github.io/jq/) to read values from YAML and JSON _files_ respectively, '
                   'if you do not wish to hand-type JSON syntax. E.g., '
                   '`elapi --OC "$(cat ~/params.yml | yq e -o json -I0)" experiments get -i <experiment ID> -F csv`.',
}
