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

from .doc import __PARAMETERS__doc__ as docs
from ..loggers import Logger
from ..plugins import experiments, bill_teams
from ..styles import get_custom_help_text
from ..styles import stdin_console, stderr_console

logger = Logger()


pretty.install()
app = typer.Typer(
    rich_markup_mode="markdown",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)

app.add_typer(bill_teams.app)
app.add_typer(experiments.app)

typer.rich_utils.STYLE_HELPTEXT = (
    ""  # fixes https://github.com/tiangolo/typer/issues/437
)
typer.rich_utils._get_help_text = (
    get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447
)


@app.command(short_help="Make `GET` requests to elabftw endpoints.")
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
    Make `GET` requests to elabftw endpoints as documented in
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
    from ..api import GETRequest
    from .helpers import CLIExport, CLIFormat
    from ..validators import Validate, HostIdentityValidator
    from ..plugins.export import Export
    from ..styles import Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if export is False:
        _export_dest = None
    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        stderr_console.print(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} get --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    data_format, export_dest, export_file_ext = CLIExport(data_format, _export_dest)
    if not query:
        format = CLIFormat(data_format, export_file_ext)
    else:
        logger.warning(
            "When --query is not empty, formatting with '--format/-F' and highlighting are disabled."
        )
        format = CLIFormat("txt", None)  # Use "txt" formatting to show binary

    session = GETRequest()
    raw_response = session(
        endpoint_name, endpoint_id, sub_endpoint_name, sub_endpoint_id, query
    )
    try:
        formatted_data = format(response_data := raw_response.json())
    except UnicodeDecodeError:
        logger.warning(
            "Response data is in binary (or not UTF-8 encoded). Data cannot be displayed properly. "
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
    short_help="Make `POST` request to elabftw endpoints.",
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
    json_: Annotated[
        str, typer.Option("--data", "-d", help=docs["data"], show_default=False)
    ] = "{}",
    # data: typer.Context = None,  TODO: To be re-enabled in Python 3.11
    file: Annotated[
        str,
        typer.Option("--file", show_default=False),
    ] = "{}",
    data_format: Annotated[
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = "json",
) -> Optional[dict]:
    """
    Make `POST` request to elabftw endpoints as documented in
    [https://doc.elabftw.net/api/v2/](https://doc.elabftw.net/api/v2/).

    <br/>
    **Example**:
    <br/>
    From [the official documentation about `POST users`](https://doc.elabftw.net/api/v2/#/Users/post-user),
    > POST /users/{id}

    With `elapi` you can do the following:
    <br/>
    `$ elapi post users --id <user id> -d '{"firstname": "John", "lastname": "Doe", "email": "test_test@itnerd.de"}'`
    will create a new user.
    """
    import ast
    from .. import APP_NAME
    from ..api import POSTRequest
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..styles import Format, Highlight
    from ..path import ProperPath

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        stderr_console.print(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} post --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    # if json_:
    try:
        data: dict = ast.literal_eval(json_)
    except SyntaxError:
        stderr_console.print(
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
        stderr_console.print(
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
            _file_comment = file["comment"]
        except KeyError:
            stderr_console.print(
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
    raw_response = session(
        endpoint_name,
        endpoint_id,
        sub_endpoint_name,
        sub_endpoint_id,
        query,
        data=data,
        files=file,
    )
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
    short_help="Make `PATCH` request to elabftw endpoints.",
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
    Make `PATCH` request to elabftw endpoints as documented in
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
    from ..api import PATCHRequest
    from json import JSONDecodeError
    from ..validators import Validate, HostIdentityValidator
    from ..styles import Format, Highlight

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        query: dict = ast.literal_eval(query)
    except SyntaxError:
        stderr_console.print(
            f"Error: Given value with --query has caused a syntax error. --query only supports JSON syntax. "
            f"See '{APP_NAME} patch --help' for more on exactly how to use --query.",
            style="red",
        )
        raise typer.Exit(1)
    try:
        data: dict = ast.literal_eval(json_)
    except SyntaxError:
        stderr_console.print(
            f"Error: Given value with --data has caused a syntax error. --data only supports JSON syntax. "
            f"See '{APP_NAME} patch --help' for more on exactly how to use --data.",
            style="red",
        )
        raise typer.Exit(1)
    session = PATCHRequest()
    raw_response = session(
        endpoint_name,
        endpoint_id,
        sub_endpoint_name,
        sub_endpoint_id,
        query,
        data=data,
    )
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


@app.command(name="show-config")
def show_config(
    show_keys: Annotated[
        Optional[bool],
        typer.Option("--show-keys", "-k", help=docs["show_keys"], show_default=True),
    ] = False,
) -> None:
    """
    Get information about detected configuration values.
    """
    from ..plugins.show_config import show

    md = Markdown(show(show_keys))
    stdin_console.print(md)


@app.command()
def version() -> str:
    """
    Show version number
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
