#!/usr/bin/python3

"""``elAPI`` is a powerful, extensible API interface to eLabFTW. It supports serving almost all kinds of requests
documented in https://doc.elabftw.net/api/v2/ with ease. elAPI treats eLabFTW API endpoints as its arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elAPI you can do the following:
        $ elapi get users --id <id>
"""

from typing import Optional

import typer
from rich import pretty
from rich.markdown import Markdown
from typing_extensions import Annotated

from ._plugin_handler import internal_plugin_typer_apps
from .doc import __PARAMETERS__doc__ as docs
from .. import APP_NAME
from ..configuration import EXPORT_DIR
from ..loggers import Logger
from ..plugins.commons.cli_helpers import OrderedCommands
from ..styles import get_custom_help_text
from ..styles import stdin_console, stderr_console

logger = Logger()


pretty.install()
app = typer.Typer(
    rich_markup_mode="markdown",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
    cls=OrderedCommands,
)

for _app in internal_plugin_typer_apps:
    app.add_typer(_app, rich_help_panel="Plugins")

typer.rich_utils.STYLE_HELPTEXT = (
    ""  # fixes https://github.com/tiangolo/typer/issues/437
)
typer.rich_utils._get_help_text = (
    get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447
)


@app.command(short_help=f"Initialize {APP_NAME} configuration file.")
def init(
    host_url: Annotated[
        str,
        typer.Option(
            "--host",
            help=docs["init_host"],
            show_default=False,
            prompt=f'Enter your {docs["init_host"][0].lower()}{docs["init_host"][1:].rstrip(".")}',
        ),
    ],
    api_token: Annotated[
        str,
        typer.Option(
            "--api-token",
            help=docs["init_api_token"],
            show_default=False,
            prompt=f'Enter your {docs["init_api_token"][0]}{docs["init_api_token"][1:].rstrip(".")}',
        ),
    ],
    export_directory: Annotated[
        str,
        typer.Option(
            "--export-dir",
            help=docs["init_export_dir"],
            show_default=False,
            prompt=f'Enter your {docs["init_export_dir"][0]}{docs["init_export_dir"][1:].rstrip(".")}',
        ),
    ] = EXPORT_DIR,
) -> None:
    """
    A quick and simple command to initialize elAPI configuration file.
    A 'host' and an 'api_token' are absolutely necessary to be able to make API calls to eLabFTW API endpoints.
    We define those values in the configuration file. elAPI is capable of multiple configuration files
    that follow an order of hierarchy. This command is meant to be user-friendly, and only creates one configuration
    file in the user's home directory. See [README](https://pypi.org/project/elapi/) for use-cases of
    advanced configuration files.

    <br/>
    'elapi init' can be run with or without any arguments. When it is run without arguments, a user prompt is shown
    asking for the required values. E.g.,
    <br/>
    Without arguments: `elapi init`
    <br/>
    With arguments: `elapi init --host <host> --api-token <api-token> --export-dir <export-directory>`

    """
    from .._names import CONFIG_FILE_NAME
    from ..configuration import LOCAL_CONFIG_LOC
    from ..validators import Validate, ValidationError
    from ..validators import PathValidator
    from ..path import ProperPath
    from time import sleep

    with stdin_console.status(
        f"Creating configuration file {CONFIG_FILE_NAME}...", refresh_per_second=15
    ):
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        try:
            validate_local_config_loc = Validate(PathValidator(LOCAL_CONFIG_LOC))
            validate_local_config_loc()
        except ValidationError:
            logger.error(
                f"{APP_NAME} couldn't validate path '{LOCAL_CONFIG_LOC}' for writing configuration! "
                f"Please make sure you have write and read access to '{LOCAL_CONFIG_LOC}'. "
                "Configuration initialization has failed!"
            )
            raise typer.Exit(1)
        else:
            path = ProperPath(LOCAL_CONFIG_LOC)
            try:
                with path.open(mode="r") as f:
                    if f.read():
                        logger.error(
                            f"A configuration file '{LOCAL_CONFIG_LOC}' already exists and it's not empty! "
                            f"It's ambiguous what to do in this situation."
                        )
                        logger.error("Configuration initialization has failed!")
                        raise typer.Exit(1)
            except path.PathException as e:
                if isinstance(e, FileNotFoundError):
                    path.create()
                else:
                    logger.error(e)
                    logger.error("Configuration initialization has failed!")
                    raise typer.Exit(1)
            try:
                with path.open(mode="w") as f:
                    _configuration_yaml_text = f"""host: {host_url}
    api_token: {api_token}
    export_dir: {export_directory}
    unsafe_api_token_warning: yes
    """
                    f.write(_configuration_yaml_text)
            except path.PathException as e:
                logger.error(e)
                logger.error("Configuration initialization has failed!")
                raise typer.Exit(1)
            else:
                stdin_console.print(
                    "Configuration file has been successfully created! "
                    f"Run '{APP_NAME} show-config' to see the configuration path "
                    "and more configuration details.",
                    style="green",
                )


@app.command(short_help="Make `GET` requests to eLabFTW endpoints.")
def get(
    endpoint_name: Annotated[
        str, typer.Argument(help=docs["endpoint_name"], show_default=False)
    ],
    endpoint_id: Annotated[
        str,
        typer.Option("--id", "-i", help=docs["endpoint_id_get"], show_default=False),
    ] = None,
    sub_endpoint_name: Annotated[
        str,
        typer.Option("--sub", help=docs["sub_endpoint_name"], show_default=False),
    ] = None,
    sub_endpoint_id: Annotated[
        str,
        typer.Option("--sub-id", help=docs["sub_endpoint_id"], show_default=False),
    ] = None,
    query: Annotated[
        str,
        typer.Option("--query", help=docs["query"], show_default=False),
    ] = "{}",
    data_format: Annotated[
        Optional[str],
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = None,
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=docs["export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
) -> dict:
    """
    Make `GET` requests to eLabFTW endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `GET users`](https://doc.elabftw.net/api/v2/#/Users/read-user),
    > GET /users/{id}

    With `elapi` you can do the following:
    <br/>
    `$ elapi get users` will return list of all users.
    <br/>
    `$ elapi get users --id <id>` will return information about the specific user `<id>`.
    """
    import ast
    import re
    from .. import APP_NAME
    from ..api import GETRequest, ElabFTWURLError
    from ..plugins.commons.cli_helpers import CLIExport, CLIFormat
    from ..validators import Validate, HostIdentityValidator
    from ..plugins.commons import Export
    from ..styles import Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if export is False:
        _export_dest = None
    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} get --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    data_format, export_dest, export_file_ext = CLIExport(data_format, _export_dest)
    if not query:
        format = CLIFormat(data_format, export_file_ext)
    else:
        logger.info(
            "When --query is not empty, formatting with '--format/-F' and highlighting are disabled."
        )
        format = CLIFormat("txt", None)  # Use "txt" formatting to show binary

    session = GETRequest()
    try:
        raw_response = session(
            endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
        )
    except ElabFTWURLError as e:
        logger.error(e)
        raise typer.Exit(1)
    try:
        formatted_data = format(response_data := raw_response.json())
    except UnicodeDecodeError:
        logger.info(
            "Response data is in binary (or not UTF-8 encoded). "
            "--export/-e will not be able to infer the data format if export path is a directory."
        )
        formatted_data = format(response_data := raw_response.content)
    if export:
        if isinstance(response_data, bytes):
            format.name = "binary"
            format.convention = "bin"
            formatted_data = response_data
        file_name_stub = f"{endpoint_name}_{endpoint_id or ''}_{sub_endpoint_name or ''}_{sub_endpoint_id or ''}"
        if query:
            _query_params = "_".join(map(lambda x: f"{x[0]}={x[1]}", query.items()))
            file_name_stub += f"_query_{_query_params}" if query else ""
        file_name_stub = re.sub(r"_{2,}", "_", file_name_stub).rstrip("_")
        export = Export(
            export_dest,
            file_name_stub=file_name_stub,
            file_extension=format.convention,
            format_name=format.name,
        )
        export(data=formatted_data, verbose=True)
    else:
        highlight = Highlight(format.name)
        if not raw_response.is_success:
            stderr_console.print(highlight(formatted_data))
            raise typer.Exit(1)
        stdin_console.print(highlight(formatted_data))
    return response_data


@app.command(
    short_help="Make `POST` request to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def post(
    endpoint_name: Annotated[
        str, typer.Argument(help=docs["endpoint_name"], show_default=False)
    ],
    *,
    endpoint_id: Annotated[
        str,
        typer.Option("--id", "-i", help=docs["endpoint_id_post"], show_default=False),
    ] = None,
    sub_endpoint_name: Annotated[
        str,
        typer.Option("--sub", help=docs["sub_endpoint_name"], show_default=False),
    ] = None,
    sub_endpoint_id: Annotated[
        str,
        typer.Option("--sub-id", help=docs["sub_endpoint_id"], show_default=False),
    ] = None,
    query: Annotated[
        str,
        typer.Option("--query", help=docs["query"], show_default=False),
    ] = "{}",
    json_: Annotated[
        str, typer.Option("--data", "-d", help=docs["data"], show_default=False)
    ] = "{}",
    # data: typer.Context = None,  TODO: To be re-enabled in Python 3.11
    file: Annotated[
        str,
        typer.Option("--file", help=docs["file_post"], show_default=False),
    ] = "{}",
    get_location: Annotated[
        bool,
        typer.Option("--get-loc", help=docs["get_loc"], show_default=False),
    ] = False,
    data_format: Annotated[
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = "json",
) -> Optional[dict]:
    """
    Make `POST` request to eLabFTW endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `POST users`](https://doc.elabftw.net/api/v2/#/Users/post-user),
    > POST /users/{id}

    With `elapi` you can do the following:
    <br/>
    `$ elapi post users -d '{"firstname": "John", "lastname": "Doe", "email": "test_test@itnerd.de"}'`
    will create a new user.
    """
    import ast
    from .. import APP_NAME
    from ..api import POSTRequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..plugins.commons import get_location_from_headers
    from ..styles import Format, Highlight
    from ..path import ProperPath

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} post --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    # if json_:
    try:
        data: dict = ast.literal_eval(json_)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --data has caused a syntax error. --data only supports JSON syntax. "
            f"See '{APP_NAME} post --help' for more on exactly how to use --data.",
            style="red",
        )
        raise typer.Exit(1)
    # else:
    # TODO: Due to strange compatibility issue between typer.context and python 3.9,
    #   passing json_ as arguments is temporarily deprecated.
    # data_keys: list[str, ...] = [_.removeprefix("--") for _ in data.args[::2]]
    # data_values: list[str, ...] = data.args[1::2]
    # data: dict[str:str, ...] = dict(zip(data_keys, data_values))
    try:
        file: Optional[dict] = ast.literal_eval(file)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --file has caused a syntax error. --file only supports JSON syntax. "
            f"See '{APP_NAME} post --help' for more on exactly how to use --file.",
            style="red",
        )
        raise typer.Exit(1)
    session = POSTRequest()
    if file:
        try:
            try:
                _file_name, _file_path = file["file"]
            except ValueError:
                _file_name = None
                _file_path = file["file"]
            try:
                _file_comment = file["comment"]
            except KeyError:
                _file_comment = None
        except KeyError:
            logger.critical(
                f"Error: Given value with --file doesn't follow the expected pattern. "
                f"See '{APP_NAME} post --help' for more on exactly how to use --file.",
                style="red",
            )
            raise typer.Exit(1)
        else:
            _file_obj = (_file_path := ProperPath(_file_path)).expanded.open(mode="rb")
            file = {
                "file": (_file_name or _file_path.expanded.name, _file_obj),
                "comment": (None, _file_comment or ""),
            }
    else:
        file = None
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            data=data,
            files=file,
        )
    except ElabFTWURLError as e:
        logger.error(e)
        raise typer.Exit(1)
    try:
        # noinspection PyUnboundLocalVariable
        _file_obj.close()
    except UnboundLocalError:
        ...

    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            if get_location:
                try:
                    _id, _url = get_location_from_headers(raw_response.headers)
                except ValueError:
                    logger.error(
                        "Request was successful but no location for resource was found!"
                    )
                    raise typer.Exit(1)
                else:
                    typer.echo(f"{_id},{_url}")
                    raise typer.Exit()
            stdin_console.print("Success: Resource created!", style="green")
        else:
            logger.error(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'.",
                style="red",
            )
            raise typer.Exit(1)
    else:
        highlight = Highlight(format.name)
        if not raw_response.is_success:
            stderr_console.print(highlight(formatted_data))
            raise typer.Exit(1)
        stdin_console.print(highlight(formatted_data))
        return formatted_data


@app.command(
    short_help="Make `PATCH` request to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def patch(
    endpoint_name: Annotated[
        str, typer.Argument(help=docs["endpoint_name"], show_default=False)
    ],
    *,
    endpoint_id: Annotated[
        str,
        typer.Option("--id", "-i", help=docs["endpoint_id_patch"], show_default=False),
    ] = None,
    sub_endpoint_name: Annotated[
        str,
        typer.Option("--sub", help=docs["sub_endpoint_name"], show_default=False),
    ] = None,
    sub_endpoint_id: Annotated[
        str,
        typer.Option("--sub-id", help=docs["sub_endpoint_id"], show_default=False),
    ] = None,
    query: Annotated[
        str,
        typer.Option("--query", help=docs["query"], show_default=False),
    ] = "{}",
    json_: Annotated[
        str, typer.Option("--data", "-d", help=docs["data_patch"], show_default=False)
    ],
    # data: typer.Context = None,  TODO: To be re-enabled in Python 3.11
    data_format: Annotated[
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = "json",
) -> Optional[dict]:
    """
    Make `PATCH` request to eLabFTW endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `PATCH users`](https://doc.elabftw.net/api/v2/#/Users/patch-user),
    > PATCH /users/{id}

    With `elapi` you can run the following to change your email address:
    <br/>
    `$ elapi patch users --id me -d '{"email": "new_email@itnerd.de"}'`.
    """
    import ast
    from .. import APP_NAME
    from ..api import PATCHRequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..styles import Format, Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} patch --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    try:
        data: dict = ast.literal_eval(json_)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --data has caused a syntax error. --data only supports JSON syntax. "
            f"See '{APP_NAME} patch --help' for more on exactly how to use --data.",
            style="red",
        )
        raise typer.Exit(1)
    session = PATCHRequest()
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            data=data,
        )
    except ElabFTWURLError as e:
        logger.error(e)
        raise typer.Exit(1)
    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            stdin_console.print("Success: Resource modified!", style="green")
        else:
            logger.error(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'.",
                style="red",
            )
            raise typer.Exit(1)
    else:
        highlight = Highlight(format.name)
        if not raw_response.is_success:
            stderr_console.print(highlight(formatted_data))
            raise typer.Exit(1)
        stdin_console.print(highlight(formatted_data))
        return formatted_data


@app.command(
    short_help="Make `DELETE` request to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def delete(
    endpoint_name: Annotated[
        str, typer.Argument(help=docs["endpoint_name"], show_default=False)
    ],
    *,
    endpoint_id: Annotated[
        str,
        typer.Option("--id", "-i", help=docs["endpoint_id_delete"], show_default=False),
    ] = None,
    sub_endpoint_name: Annotated[
        str,
        typer.Option("--sub", show_default=False),
    ] = None,
    sub_endpoint_id: Annotated[
        str,
        typer.Option("--sub-id", show_default=False),
    ] = None,
    query: Annotated[
        str,
        typer.Option("--query", show_default=False),
    ] = "{}",
    data_format: Annotated[
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = "json",
) -> Optional[dict]:
    """
    Make `DELETE` request to eLabFTW endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `Delete items`](https://doc.elabftw.net/api/v2/#/Items/delete-item),
    > DELETE /items/{id}

    With `elapi` you can run the following to delete an item:
    <br/>
    `$ elapi delete item --id <item ID>`.
    <br/>
    Run the following to delete a tag:
    <br/>
    `$ elapi delete experiments -i <experiment ID> --sub tags --sub-id <tag ID>`
    """
    import ast
    from .. import APP_NAME
    from ..api import DELETERequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..styles import Format, Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        logger.critical(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} patch --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)

    session = DELETERequest()
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
        )
    except ElabFTWURLError as e:
        logger.error(e)
        raise typer.Exit(1)
    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            stdin_console.print("Success: Resource deleted!", style="green")
        else:
            logger.error(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'.",
                style="red",
            )
            raise typer.Exit(1)
    else:
        highlight = Highlight(format.name)
        if not raw_response.is_success:
            stderr_console.print(highlight(formatted_data))
            raise typer.Exit(1)
        stdin_console.print(highlight(formatted_data))
        return formatted_data


@app.command(name="show-config")
def show_config(
    no_keys: Annotated[
        Optional[bool],
        typer.Option("--no-keys", help=docs["no_keys"], show_default=True),
    ] = False,
) -> None:
    """
    Get information about detected configuration values.
    """
    from ..plugins.show_config import show

    md = Markdown(show(no_keys))
    stdin_console.print(md)


@app.command()
def version() -> str:
    """
    Show version number.
    """
    from ..plugins.version import elapi_version

    _version = elapi_version()
    typer.echo(_version)
    return _version


@app.command(
    hidden=True, deprecated=True
)  # deprecated instead of removing for future use
def cleanup() -> None:
    """
    Remove cached data.
    """
    from ..configuration import TMP_DIR
    from ..path import ProperPath
    from time import sleep

    with stdin_console.status("Cleaning up...", refresh_per_second=15):
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        ProperPath(TMP_DIR, err_logger=logger).remove(verbose=True)
    stdin_console.print("Done!", style="green")
