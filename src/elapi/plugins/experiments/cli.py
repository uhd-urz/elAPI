from typing import Annotated, Optional

import typer

from ._doc import __PARAMETERS__doc__ as docs
from .experiments import (
    ExperimentIDValidator,
    FixedExperimentEndpoint,
    append_to_experiment,
)
from ...cli.doc import __PARAMETERS__doc__ as elapi_docs
from ...configuration import get_active_export_dir
from ...core_validators import ValidationError
from ...loggers import Logger
from ...plugins.commons.cli_helpers import CLIExport, CLIFormat, Typer
from ...styles import stdout_console, stderr_console
from ...utils.typer_patches import patch_typer_flag_value

logger = Logger()

patch_typer_flag_value()
app = Typer(name="experiments", help="Manage experiments.")


# noinspection PyCallingNonCallable,PyUnresolvedReferences
@app.command(short_help="Read or download an experiment.")
def get(
    experiment_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["experiment_id"], show_default=False)
    ],
    data_format: Annotated[
        Optional[str],
        typer.Option("--format", "-F", help=docs["data_format"], show_default=False),
    ] = None,
    highlight_syntax: Annotated[
        Optional[bool],
        typer.Option(
            "--highlight",
            "-H",
            help=elapi_docs["highlight_syntax"],
            show_default=True,
        ),
    ] = False,
    export: Annotated[
        Optional[str],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + docs["export_details"],
            is_flag=False,
            flag_value="",
            show_default=False,
        ),
    ] = None,
    export_overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
        ),
    ] = False,
) -> dict:
    """
    Read or download an experiment.
    """
    import sys
    from ...core_validators import Validate
    from ...api import GlobalSharedSession
    from ...api.validators import HostIdentityValidator
    from ..commons import Export
    from ...styles import Highlight
    from .formats import BinaryFormat
    from ...core_validators import Exit

    with GlobalSharedSession(limited_to="sync"):
        validate_config = Validate(HostIdentityValidator())
        validate_config()

        if export == "":
            export = get_active_export_dir()
        try:
            experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
        except ValidationError as e:
            logger.error(e)
            raise typer.Exit(1)
        else:
            data_format, export_dest, export_file_ext = CLIExport(
                data_format, export, export_overwrite
            )
            format = CLIFormat(data_format, __package__, export_file_ext)

            experiment_name: str = f"experiment_{experiment_id}"
            if isinstance(format, BinaryFormat):
                if export is not None:
                    logger.info(
                        f"Data with format '{data_format}' cannot be shown on the terminal. "
                        f"Data will be exported."
                    )
                export = get_active_export_dir()
                with stdout_console.status(
                    f"Getting {experiment_name}...", refresh_per_second=15
                ):
                    response = FixedExperimentEndpoint().get(
                        experiment_id, query={"format": data_format.lower()}
                    )
                formatted_data = format(response_data := response.content)
            else:
                response = FixedExperimentEndpoint().get(experiment_id)
                formatted_data = format(response_data := response.json())

            if export is not None:
                file_name_stub = experiment_name
                export_response = Export(
                    export_dest,
                    file_name_stub=file_name_stub,
                    file_extension=format.convention,
                    format_name=format.name,
                )
                export_response(data=formatted_data, verbose=True)
            else:
                if highlight_syntax is True:
                    highlight = Highlight(format.name, package_identifier=__package__)
                    if not response.is_success:
                        stderr_console.print(highlight(formatted_data))
                        raise Exit(1)
                    stdout_console.print(highlight(formatted_data))
                else:
                    if not response.is_success:
                        typer.echo(formatted_data, file=sys.stderr)
                        raise Exit(1)
                    typer.echo(formatted_data)
            response.close()
            return response_data


@app.command(short_help="Add new content to an existing experiment.")
def append(
    experiment_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["experiment_id"], show_default=False)
    ],
    content_text: Annotated[
        Optional[str],
        typer.Option(
            "--text", "-t", help=docs["append_content_text"], show_default=False
        ),
    ] = None,
    content_path: Annotated[
        Optional[str],
        typer.Option(
            "--path", "-P", help=docs["append_content_path"], show_default=False
        ),
    ] = None,
    markdown_to_html: Annotated[
        Optional[bool],
        typer.Option(
            "--markdown-to-html",
            "-M",
            help=docs["append_markdown_to_html"],
            show_default=False,
        ),
    ] = False,
) -> str:
    """
    Add new content to an existing experiment.
    """
    from ...core_validators import Validate
    from ...api import GlobalSharedSession
    from ...api.validators import HostIdentityValidator
    from ...path import ProperPath

    with GlobalSharedSession(limited_to="sync"):
        validate_config = Validate(HostIdentityValidator())
        validate_config()
        try:
            experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
        except ValidationError as e:
            logger.error(e)
            raise typer.Exit(1)
        else:
            if content_text and content_path:
                logger.error(
                    "Either '--text/-t' or '--path/-P' can be defined, not both!"
                )
                raise typer.Exit(1)
            if content_text is not None:
                content: str = content_text
            elif content_path is not None:
                if not (content_path := ProperPath(content_path)).kind == "file":
                    logger.error(f" Given path '{content_path}' must be a file!")
                    raise typer.Exit(1)
                with content_path.open() as f:
                    try:
                        content: str = f.read()
                    except UnicodeDecodeError:
                        logger.error("File in given path must be UTF-8 encoded!")
                        raise typer.Exit(1)
            else:
                content: str = ""
            if not content:
                stdout_console.print(
                    "[yellow]Content is empty. Nothing was appended to experiment.[/yellow]"
                )
                raise typer.Exit()
            append_to_experiment(experiment_id, content, markdown_to_html)
            stdout_console.print(
                "[green]Successfully appended content to experiment.[/green]"
            )
            return content


@app.command(short_help="Attach a file to an experiment.")
def upload_attachment(
    experiment_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["experiment_id"], show_default=False)
    ],
    path: Annotated[
        str,
        typer.Option(
            "--path", "-P", help=docs["upload_attachment_path"], show_default=False
        ),
    ],
    attachment_name: Annotated[
        Optional[str],
        typer.Option(
            "--rename", "-n", help=docs["upload_attachment_rename"], show_default=False
        ),
    ] = None,
    comment: Annotated[
        Optional[str],
        typer.Option(
            "--comment",
            "-c",
            help=docs["upload_attachment_comment"],
            show_default=False,
        ),
    ] = None,
) -> None:
    """
    Add a file to an existing experiment.
    """
    from ...core_validators import Validate
    from ...api.validators import HostIdentityValidator
    from ...api import GlobalSharedSession
    from .experiments import attach_to_experiment

    with GlobalSharedSession(limited_to="sync"):
        validate_config = Validate(HostIdentityValidator())
        validate_config()
        try:
            experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
        except ValidationError as e:
            logger.error(e)
            raise typer.Exit(1)
        else:
            with stdout_console.status(
                "Uploading attachment...", refresh_per_second=15
            ):
                attach_to_experiment(
                    experiment_id,
                    file_path=path,
                    attachment_name=attachment_name,
                    comment=comment,
                )
            stdout_console.print("[green]Successfully attached to experiment.[/green]")


@app.command(short_help="Download an attachment from an experiment.")
def download_attachment(
    experiment_id: Annotated[
        str, typer.Option("--id", "-i", help=docs["experiment_id"], show_default=False)
    ],
    attachment_id: Annotated[
        str,
        typer.Option(
            "--attachment-id",
            "-a",
            help=docs["download_attachment_attachment_id"],
            show_default=False,
        ),
    ],
    export: Annotated[
        Optional[str],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + docs["export_details"],
            is_flag=False,
            flag_value="",
            show_default=False,
        ),
    ] = None,
    export_overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite", help=elapi_docs["export_overwrite"], show_default=False
        ),
    ] = False,
) -> None:
    """
    Download an attachment from an experiment.
    """
    from ...core_validators import Validate
    from ...api.validators import HostIdentityValidator
    from ...api import GlobalSharedSession
    from ...plugins.commons import Export
    from .experiments import download_attachment

    with GlobalSharedSession(limited_to="sync"):
        validate_config = Validate(HostIdentityValidator())
        validate_config()

        if (
            export == "" or export is None
        ):  # exporting is the default for downloading attachment
            export = get_active_export_dir()
        try:
            experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
        except ValidationError as e:
            logger.error(e)
            raise typer.Exit(1)
        else:
            try:
                with stdout_console.status(
                    "Downloading attachment...", refresh_per_second=15
                ):
                    (
                        attachment,
                        attachment_real_id,
                        attachment_name,
                        attachment_extension,
                        attachment_hash,
                        attachment_creation_date,
                    ) = download_attachment(experiment_id, attachment_id)
            except ValueError as e:
                logger.error(e)
                raise typer.Exit(1)
            else:
                data_format, export_dest, export_file_ext = CLIExport(
                    attachment_extension, export, export_overwrite
                )
                _is_real_id = attachment_id == attachment_real_id
                if export is not None:
                    if export_file_ext and export_file_ext != attachment_extension:
                        logger.info(
                            f"File extension is '{export_file_ext}' but "
                            f"data format will be '{attachment_extension}'."
                        )
                    file_name_stub = (
                        f"attachment_{attachment_real_id if _is_real_id else attachment_hash[:6]}_"
                        f"{attachment_name}"
                    )
                    export_attachment = Export(
                        export_dest,
                        file_name_stub=file_name_stub,
                        file_extension=attachment_extension,
                        format_name=data_format,
                    )
                    export_attachment(data=attachment, verbose=True)
