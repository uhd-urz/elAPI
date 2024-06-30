#!/usr/bin/python3

"""``elAPI`` is a powerful, extensible API interface to eLabFTW. It supports serving almost all kinds of requests
documented in https://doc.elabftw.net/api/v2/ with ease. elAPI treats eLabFTW API endpoints as its arguments.

**Example**::

    From https://doc.elabftw.net/api/v2/#/Users/read-user:
        > GET /users/{id}

    With elAPI you can do the following:
        $ elapi get users --id <id>
"""

import logging
from functools import partial
from typing import Optional

import typer
from rich import pretty
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

from ._plugin_handler import PluginInfo
from ._plugin_handler import (
    internal_plugin_typer_apps,
    external_local_plugin_typer_apps,
)
from .doc import __PARAMETERS__doc__ as docs
from .. import APP_NAME
from ..configuration import FALLBACK_EXPORT_DIR
from ..loggers import Logger, FileLogger
from ..plugins.commons.cli_helpers import Typer
from ..styles import get_custom_help_text
from ..styles import stdin_console, stderr_console, rich_format_help_with_callback

logger = Logger()
file_logger = FileLogger()
pretty.install()


app = Typer()
SENSITIVE_PLUGIN_NAMES: tuple[str, str, str] = ("init", "show-config", "version")
SPECIAL_SENSITIVE_PLUGIN_NAMES: tuple[str] = ("show-config",)
COMMANDS_TO_SKIP_CLI_STARTUP: list = list(SENSITIVE_PLUGIN_NAMES)
CLI_STARTUP_CALLBACK_PANEL_NAME: str = f"{APP_NAME} global options"
RESERVED_PLUGIN_NAMES: tuple[str, ...] = (
    "apikeys",
    "config",
    "info",
    "items",
    "events",
    "todolist",
    "users",
    "idps",
    "import",
    "exports",
    APP_NAME,
)
INTERNAL_PLUGIN_NAME_REGISTRY: dict = {}
EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY: dict = {}

INTERNAL_PLUGIN_PANEL_NAME: str = "Built-in plugins"
THIRD_PARTY_PLUGIN_PANEL_NAME: str = "Third-party plugins"


@app.callback()
def cli_startup(
    override_config: Annotated[
        Optional[str],
        typer.Option(
            "--override-config",
            "--OC",
            help=docs["cli_startup"],
            show_default=False,
            rich_help_panel=CLI_STARTUP_CALLBACK_PANEL_NAME,
        ),
    ] = "{}",
) -> type(None):
    import click
    from sys import argv
    from ..styles import print_typer_error
    from ..configuration import (
        KEY_API_TOKEN,
        AppliedConfigIdentity,
        minimal_active_configuration,
    )
    from ..configuration.config import APIToken
    from ..configuration.validators import MainConfigurationValidator
    from ..core_validators import Exit
    from ..configuration import reinitiate_config
    from ..plugins.commons.get_data_from_input_or_path import get_structured_data

    try:
        override_config: dict = get_structured_data(
            override_config, option_name="--override-config/--OC"
        )
    except ValueError:
        raise Exit(1)
    else:
        OVERRIDABLE_FIELDS_SOURCE: str = "CLI"
        for key, value in override_config.items():
            if key.lower() == KEY_API_TOKEN.lower():
                try:
                    minimal_active_configuration[key.upper()] = AppliedConfigIdentity(
                        APIToken(value), OVERRIDABLE_FIELDS_SOURCE
                    )
                except ValueError:
                    minimal_active_configuration[key.upper()] = AppliedConfigIdentity(
                        value, OVERRIDABLE_FIELDS_SOURCE
                    )
            else:
                minimal_active_configuration[key.upper()] = AppliedConfigIdentity(
                    value, OVERRIDABLE_FIELDS_SOURCE
                )
        if (
            (
                calling_sub_command_name := (
                    ctx := click.get_current_context()
                ).invoked_subcommand
            )
            not in COMMANDS_TO_SKIP_CLI_STARTUP
            and ctx.command.name != calling_sub_command_name
        ):
            if argv[-1] != (ARG_TO_SKIP := "--help") or ARG_TO_SKIP not in argv:
                if override_config or not MainConfigurationValidator.ALREADY_VALIDATED:
                    reinitiate_config()
        else:
            if calling_sub_command_name in SENSITIVE_PLUGIN_NAMES:
                if override_config:
                    print_typer_error(
                        f"{APP_NAME} command '{calling_sub_command_name}' does not support "
                        f"the override argument --override-config/--OC."
                    )
                    raise Exit(1)
                if calling_sub_command_name in SPECIAL_SENSITIVE_PLUGIN_NAMES:
                    reinitiate_config(ignore_essential_validation=True)


def cli_startup_for_plugins(
    override_config: Annotated[
        Optional[str],
        typer.Option(
            "--override-config",
            "--OC",
            help=docs["cli_startup"],
            show_default=False,
            rich_help_panel=CLI_STARTUP_CALLBACK_PANEL_NAME,
        ),
    ] = None,
):
    from ..styles import print_typer_error
    from ..validators import Exit

    if override_config is not None:
        print_typer_error(
            f"--override-config/--OC can only be passed after "
            f"the main program name '{APP_NAME}', and not after a plugin name."
        )
        raise Exit(1)
    return cli_startup()


for _app in internal_plugin_typer_apps:
    if _app is not None:
        INTERNAL_PLUGIN_NAME_REGISTRY[app_name := _app.info.name] = _app
        COMMANDS_TO_SKIP_CLI_STARTUP.append(_app.info.name)
        app.add_typer(
            _app,
            rich_help_panel=INTERNAL_PLUGIN_PANEL_NAME,
            callback=cli_startup_for_plugins,
        )


def disable_plugin(
    main_app: Typer, /, *, plugin_name: str, err_msg: str, panel_name: str
):
    from ..utils import add_message

    add_message(err_msg, logging.WARNING)
    for i, registered_app in enumerate(main_app.registered_groups):
        if plugin_name == registered_app.typer_instance.info.name:
            main_app.registered_groups.pop(i)
            break

    @main_app.command(
        name=plugin_name,
        rich_help_panel=panel_name,
        help="🚫️ Disabled due to name conflict. See `--help` or log file to know more.",
    )
    def name_conflict_error():
        from ..core_validators import Exit

        logger.error(err_msg)
        raise Exit(1)


def messages_panel():
    from ..styles import NoteText
    from ..configuration import CONFIG_FILE_NAME
    from ..loggers import FileLogger
    from rich.logging import RichHandler
    from ..utils import MessagesList

    messages = MessagesList()

    if messages:
        handler = RichHandler(show_path=False, show_time=False)
        log_record = logging.LogRecord(
            logger.name,
            level=logging.NOTSET,
            pathname="",
            lineno=0,
            msg="",
            args=None,
            exc_info=None,
        )
        grid = Table.grid(expand=True, padding=1)
        grid.add_column(style="bold")
        grid.add_column()
        for i, log_tuple in enumerate(messages, start=1):
            message, level, logger_ = log_tuple.__dict__.values()
            FileLogger().log(level, message) if logger_ is None else logger_.log(
                level, message
            )
            log_record.levelno = log_tuple.level
            log_record.levelname = logging.getLevelName(log_tuple.level)
            # The following is the only way that I could figure out for the log
            # message to show up in rich panel without breaking the pretty rich formatting.
            message = handler.render(
                record=log_record,
                traceback=None,
                message_renderable=handler.render_message(
                    record=log_record,
                    message=log_tuple.message,
                ),
            )
            grid.add_row(f"{i}.", message)
        logger.handlers[-1]._log_render.show_path = True
        grid.add_row(
            "",
            NoteText(
                f"{APP_NAME} will continue to work despite the above warnings. "
                f"Set [dim]development_mode: True[/dim] in {CONFIG_FILE_NAME} configuration "
                "file to debug these errors with Python traceback (if any).",
                stem="Note",
            ),
        )
        stderr_console.print(
            Panel(
                grid,
                title=f"[yellow]ⓘ Message{'s' if len(messages) > 1 else ''}[/yellow]",
                title_align="left",
            )
        )


typer.rich_utils.rich_format_help = partial(
    rich_format_help_with_callback, result_callback=messages_panel
)

typer.rich_utils.STYLE_HELPTEXT = (
    ""  # fixes https://github.com/tiangolo/typer/issues/437
)
typer.rich_utils._get_help_text = (
    get_custom_help_text  # fixes https://github.com/tiangolo/typer/issues/447
)

RAW_API_COMMANDS_PANEL_NAME: str = "Raw API commands"


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
        Optional[str],
        typer.Option(
            "--export-dir",
            help=docs["init_export_dir"],
            show_default=False,
            prompt=f'Enter your {docs["init_export_dir"][0]}{docs["init_export_dir"][1:].rstrip(".")}',
        ),
    ] = FALLBACK_EXPORT_DIR,
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
    from ..core_validators import Validate, ValidationError
    from ..core_validators import PathValidator
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
unsafe_api_token_warning: true
enable_http2: false
verify_ssl: true
timeout: 5
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


@app.command(
    short_help="Make `GET` requests to eLabFTW endpoints.",
    rich_help_panel=RAW_API_COMMANDS_PANEL_NAME,
)
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
    export_overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help=docs["export_overwrite"], show_default=False),
    ] = False,
    headers: Annotated[
        Optional[str],
        typer.Option("--headers", help=docs["headers"], show_default=False),
    ] = "{}",
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
    from httpx import ConnectError
    from ssl import SSLError
    import re
    from ..api import GETRequest, ElabFTWURLError
    from ..plugins.commons.cli_helpers import CLIExport, CLIFormat
    from ..plugins.commons import get_structured_data
    from ..core_validators import Validate
    from ..api.validators import HostIdentityValidator
    from ..plugins.commons import Export
    from ..styles import Highlight, print_typer_error, NoteText
    from ..core_validators import Exit
    from ..configuration import get_active_host

    validate_identity = Validate(HostIdentityValidator())
    validate_identity()

    if export is False:
        _export_dest = None
    try:
        query: dict = get_structured_data(query, option_name="--query")
    except ValueError:
        raise Exit(1)
    try:
        headers: dict = get_structured_data(headers, option_name="--headers")
    except ValueError:
        raise Exit(1)
    data_format, export_dest, export_file_ext = CLIExport(
        data_format, _export_dest, export_overwrite
    )
    if not query:
        format = CLIFormat(data_format, export_file_ext)
    else:
        logger.info(
            "When --query is not empty, formatting with '--format/-F' and highlighting are disabled."
        )
        format = CLIFormat("txt", None)  # Use "txt" formatting to show binary

    try:
        session = GETRequest()
    except SSLError as e:
        logger.error(e)
        raise Exit() from e
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            headers=headers,
        )
    except (AttributeError, TypeError) as e:
        err_msg = (
            f"Given data was successfully parsed but there was an error while processing it. "
            f'Exception details: "{e.__class__.__name__}: {e}".'
        )
        file_logger.error(err_msg)
        print_typer_error(err_msg)
        stdin_console.print(
            NoteText(
                "See --help for examples of how to pass values in JSON format.",
                stem="Note",
            )
        )
        raise Exit(1)
    except ElabFTWURLError as e:
        file_logger.error(e)
        print_typer_error(f"{e}")
        raise Exit(1) from e
    except ConnectError as e:
        logger.error(
            f"{APP_NAME} failed to establish a connection to host '{get_active_host()}'. "
            f"Exception details: {e}"
        )
        raise Exit(1) from e
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
    short_help="Make `POST` requests to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    rich_help_panel=RAW_API_COMMANDS_PANEL_NAME,
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
    headers: Annotated[
        Optional[str],
        typer.Option("--headers", help=docs["headers"], show_default=False),
    ] = "{}",
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
    from httpx import ConnectError
    from ssl import SSLError
    from .. import APP_NAME
    from ..api import POSTRequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..core_validators import Validate
    from ..api.validators import HostIdentityValidator
    from ..plugins.commons import get_location_from_headers
    from ..plugins.commons import get_structured_data
    from ..styles import Format, Highlight, print_typer_error, NoteText
    from ..core_validators import Exit
    from ..path import ProperPath
    from ..configuration import get_active_host

    validate_identity = Validate(HostIdentityValidator())
    validate_identity()

    try:
        query: dict = get_structured_data(query, option_name="--query")
    except ValueError:
        raise Exit(1)
    try:
        headers: dict = get_structured_data(headers, option_name="--headers")
    except ValueError:
        raise Exit(1)
    try:
        data: dict = get_structured_data(json_, option_name="--data/-d")
    except ValueError:
        raise Exit(1)
    # else:
    # TODO: Due to strange compatibility issue between typer.context and python 3.9,
    #   passing json_ as arguments is temporarily deprecated.
    # data_keys: list[str, ...] = [_.removeprefix("--") for _ in data.args[::2]]
    # data_values: list[str, ...] = data.args[1::2]
    # data: dict[str:str, ...] = dict(zip(data_keys, data_values))
    try:
        file: Optional[dict] = get_structured_data(file, option_name="--file")
    except ValueError:
        raise Exit(1)
    try:
        session = POSTRequest()
    except SSLError as e:
        logger.error(e)
        raise Exit() from e
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
                f"See '{APP_NAME} post --help' for more on exactly how to use --file."
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
            headers=headers,
        )
    except (AttributeError, TypeError) as e:
        err_msg = (
            f"Given data was successfully parsed but there was an error while processing it. "
            f'Exception details: "{e.__class__.__name__}: {e}".'
        )
        file_logger.error(err_msg)
        print_typer_error(err_msg)
        stdin_console.print(
            NoteText(
                "See --help for examples of how to pass values in JSON format.",
                stem="Note",
            )
        )
        raise Exit(1)
    except ElabFTWURLError as e:
        file_logger.error(e)
        print_typer_error(f"{e}")
        raise Exit(1) from e
    except ConnectError as e:
        logger.error(
            f"{APP_NAME} failed to establish a connection to host '{get_active_host()}'. "
            f"Exception details: {e}"
        )
        raise Exit(1) from e
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
                f"The HTTP return was: '{raw_response}'."
            )
            stdin_console.print(
                NoteText(
                    "This error can occur if you are passing any invalid JSON.",
                    stem="Hint",
                )
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
    short_help="Make `PATCH` requests to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    rich_help_panel=RAW_API_COMMANDS_PANEL_NAME,
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
    headers: Annotated[
        Optional[str],
        typer.Option("--headers", help=docs["headers"], show_default=False),
    ] = "{}",
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
    from httpx import ConnectError
    from ssl import SSLError
    from ..api import PATCHRequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..core_validators import Validate
    from ..api.validators import HostIdentityValidator
    from ..styles import Format, Highlight, NoteText, print_typer_error
    from ..core_validators import Exit
    from ..configuration import get_active_host
    from ..plugins.commons import get_structured_data

    validate_identity = Validate(HostIdentityValidator())
    validate_identity()

    try:
        query: dict = get_structured_data(query, option_name="--query")
    except ValueError:
        raise Exit(1)
    try:
        headers: dict = get_structured_data(headers, option_name="--headers")
    except ValueError:
        raise Exit(1)
    try:
        data: dict = get_structured_data(json_, option_name="--data/-d")
    except ValueError:
        raise Exit(1)
    try:
        session = PATCHRequest()
    except SSLError as e:
        logger.error(e)
        raise Exit() from e
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            data=data,
            headers=headers,
        )
    except (AttributeError, TypeError) as e:
        err_msg = (
            f"Given data was successfully parsed but there was an error while processing it. "
            f'Exception details: "{e.__class__.__name__}: {e}".'
        )
        file_logger.error(err_msg)
        print_typer_error(err_msg)
        stdin_console.print(
            NoteText(
                "See --help for examples of how to pass values in JSON format.",
                stem="Note",
            )
        )
        raise Exit(1)
    except ElabFTWURLError as e:
        file_logger.error(e)
        print_typer_error(f"{e}")
        raise Exit(1) from e
    except ConnectError as e:
        logger.error(
            f"{APP_NAME} failed to establish a connection to host '{get_active_host()}'. "
            f"Exception details: {e}"
        )
        raise Exit(1) from e
    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            stdin_console.print("Success: Resource modified!", style="green")
        else:
            logger.error(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'."
            )
            stdin_console.print(
                NoteText(
                    "This error can occur if you are passing any invalid JSON.",
                    stem="Hint",
                )
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
    short_help="Make `DELETE` requests to eLabFTW endpoints.",
    # context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    rich_help_panel=RAW_API_COMMANDS_PANEL_NAME,
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
        str,
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = "json",
    headers: Annotated[
        Optional[str],
        typer.Option("--headers", help=docs["headers"], show_default=False),
    ] = "{}",
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
    from httpx import ConnectError
    from ssl import SSLError
    from ..api import DELETERequest, ElabFTWURLError
    from json import JSONDecodeError
    from ..core_validators import Validate
    from ..api.validators import HostIdentityValidator
    from ..styles import Format, Highlight, NoteText, print_typer_error
    from ..core_validators import Exit
    from ..configuration import get_active_host
    from ..plugins.commons import get_structured_data

    validate_identity = Validate(HostIdentityValidator())
    validate_identity()

    try:
        query: dict = get_structured_data(query, option_name="--query")
    except ValueError:
        raise Exit(1)
    try:
        headers: dict = get_structured_data(headers, option_name="--headers")
    except ValueError:
        raise Exit(1)
    try:
        session = DELETERequest()
    except SSLError as e:
        logger.error(e)
        raise Exit() from e
    try:
        raw_response = session(
            endpoint_name,
            endpoint_id,
            sub_endpoint_name,
            sub_endpoint_id,
            query,
            headers=headers,
        )
    except (AttributeError, TypeError) as e:
        err_msg = (
            f"Given data was successfully parsed but there was an error while processing it. "
            f'Exception details: "{e.__class__.__name__}: {e}".'
        )
        file_logger.error(err_msg)
        print_typer_error(err_msg)
        stdin_console.print(
            NoteText(
                "See --help for examples of how to pass values in JSON format.",
                stem="Note",
            )
        )
        raise Exit(1)
    except ElabFTWURLError as e:
        file_logger.error(e)
        print_typer_error(f"{e}")
        raise Exit(1) from e
    except ConnectError as e:
        logger.error(
            f"{APP_NAME} failed to establish a connection to host '{get_active_host()}'. "
            f"Exception details: {e}"
        )
        raise Exit(1) from e
    format = Format(data_format)
    try:
        formatted_data = format(raw_response.json())
    except JSONDecodeError:
        if raw_response.is_success:
            stdin_console.print("Success: Resource deleted!", style="green")
        else:
            logger.error(
                f"Warning: Something unexpected happened! "
                f"The HTTP return was: '{raw_response}'."
            )
            stdin_console.print(
                NoteText(
                    "This error can occur if you are passing any invalid JSON.",
                    stem="Hint",
                )
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


for plugin_info in external_local_plugin_typer_apps:
    if plugin_info is not None:
        _app, path = plugin_info
    else:
        continue
    if _app is not None:
        original_name: str = _app.info.name
        app_name: str = original_name.lower()
        if app_name in EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY:
            error_message = (
                f"Plugin name '{original_name}' from {path} conflicts with an "
                f"existing third-party plugin from {EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[app_name].path}. "
                f"Please rename the plugin."
            )
            error_message += (
                " Note, plugin names are case-insensitive."
                if original_name != app_name
                else ""
            )
            disable_plugin(
                app,
                plugin_name=app_name,
                err_msg=error_message,
                panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
            )
        elif app_name in INTERNAL_PLUGIN_NAME_REGISTRY:
            error_message = (
                f"Plugin name '{original_name}' from {path} conflicts with an "
                f"existing built-in plugin name. "
                f"Please rename the plugin."
            )
            error_message += (
                " Note, plugin names are case-insensitive."
                if original_name != app_name
                else ""
            )
            disable_plugin(
                app,
                plugin_name=app_name,
                err_msg=error_message,
                panel_name=INTERNAL_PLUGIN_PANEL_NAME,
            )
        elif app_name in RESERVED_PLUGIN_NAMES:
            error_message = (
                f"Plugin name '{original_name}' from {path} conflicts with an "
                f"reserved name. "
                f"Please rename the plugin."
            )
            error_message += (
                " Note, plugin names are case-insensitive."
                if original_name != app_name
                else ""
            )
            disable_plugin(
                app,
                plugin_name=app_name,
                err_msg=error_message,
                panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
            )
        else:
            EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[app_name] = PluginInfo(_app, path)
            COMMANDS_TO_SKIP_CLI_STARTUP.append(app_name)
            app.add_typer(
                _app,
                rich_help_panel=THIRD_PARTY_PLUGIN_PANEL_NAME,
                callback=cli_startup_for_plugins,
            )
