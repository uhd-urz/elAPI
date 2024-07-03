from typing import Annotated, Optional

import typer

from ._doc import __PARAMETERS__doc__ as docs
from .experiments import (
    ExperimentIDValidator,
    FixedExperimentEndpoint,
    append_to_experiment,
)
from ...cli.doc import __PARAMETERS__doc__ as elapi_docs
from ...core_validators import ValidationError
from ...loggers import Logger
from ...plugins.commons.cli_helpers import CLIExport, CLIFormat, Typer
from ...styles import stdin_console, stderr_console

logger = Logger()


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
    export: Annotated[
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
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
    from ...core_validators import Validate
    from ...api.validators import HostIdentityValidator
    from ..commons import Export
    from ...styles import Highlight
    from . import (
        formats,
    )  # must be imported for all formats to be registered by BaseFormat

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if export is False:
        _export_dest = None
    try:
        experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
    except ValidationError as e:
        logger.error(e)
        raise typer.Exit(1)
    else:
        data_format, export_dest, export_file_ext = CLIExport(
            data_format, _export_dest, export_overwrite
        )
        format = CLIFormat(data_format, export_file_ext)

        if isinstance(format, formats.BinaryFormat):
            if not export:
                logger.info(
                    f"Data with format '{data_format}' cannot be shown on the terminal. "
                    f"Data will be exported."
                )
            export = True
            response = FixedExperimentEndpoint().get(
                experiment_id, query={"format": data_format.lower()}
            )
            formatted_data = format(response_data := response.content)
        else:
            response = FixedExperimentEndpoint().get(experiment_id)
            formatted_data = format(response_data := response.json())

        if export:
            file_name_stub = (
                f"experiment_{experiment_id}" if experiment_id else "experiment"
            )
            export = Export(
                export_dest,
                file_name_stub=file_name_stub,
                file_extension=format.convention,
                format_name=format.name,
            )
            export(data=formatted_data, verbose=True)
        else:
            highlight = Highlight(format.name)
            if not response.is_success:
                stderr_console.print(highlight(formatted_data))
                raise typer.Exit(1)
            stdin_console.print(highlight(formatted_data))
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
    from ...api.validators import HostIdentityValidator
    from ...path import ProperPath

    validate_config = Validate(HostIdentityValidator())
    validate_config()
    try:
        experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
    except ValidationError as e:
        logger.error(e)
        raise typer.Exit(1)
    else:
        if content_text and content_path:
            logger.error("Either '--text/-t' or '--path/-P' can be defined, not both!")
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
            stdin_console.print(
                "[yellow]Content is empty. Nothing was appended to experiment.[/yellow]"
            )
            raise typer.Exit()
        append_to_experiment(experiment_id, content, markdown_to_html)
        stdin_console.print(
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
    from .experiments import attach_to_experiment

    validate_config = Validate(HostIdentityValidator())
    validate_config()
    try:
        experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
    except ValidationError as e:
        logger.error(e)
        raise typer.Exit(1)
    else:
        attach_to_experiment(
            experiment_id,
            file_path=path,
            attachment_name=attachment_name,
            comment=comment,
        )
        stdin_console.print("[green]Successfully attached to experiment.[/green]")


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
        Optional[bool],
        typer.Option(
            "--export",
            "-e",
            help=elapi_docs["export"] + docs["export_details"],
            is_flag=True,
            is_eager=True,
            show_default=False,
        ),
    ] = False,
    _export_dest: Annotated[Optional[str], typer.Argument(hidden=True)] = None,
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
    from ...plugins.commons import Export
    from .experiments import download_attachment

    validate_config = Validate(HostIdentityValidator())
    validate_config()

    if export is False:
        _export_dest = None
    export = True  # export is always true for downloading attachment
    try:
        experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
    except ValidationError as e:
        logger.error(e)
        raise typer.Exit(1)
    else:
        try:
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
                attachment_extension, _export_dest, export_overwrite
            )
            _is_real_id = attachment_id == attachment_real_id
            if export:
                if export_file_ext and export_file_ext != attachment_extension:
                    logger.info(
                        f"File extension is '{export_file_ext}' but data format will be '{attachment_extension}'."
                    )
                file_name_stub = f"attachment_{attachment_real_id if _is_real_id else attachment_hash[:6]}_{attachment_name}"
                export = Export(
                    export_dest,
                    file_name_stub=file_name_stub,
                    file_extension=attachment_extension,
                    format_name=data_format,
                )
                export(data=attachment, verbose=True)
