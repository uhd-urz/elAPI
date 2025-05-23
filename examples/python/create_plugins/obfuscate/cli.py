from typing import Optional, Annotated

import typer
from elapi.api import GlobalSharedSession
from elapi.plugins.commons import Typer

from ._cli_helpers import _obfuscate_entity, _revert_obfuscated_entity
from .names import (
    FIELD_NAME,
)

app = Typer(name="obfuscate", help="Obfuscate entities in bulk.")


@app.command("experiments", help="Obfuscate all experiment titles.")
def obfuscate_experiments(
    extra_field_name: Annotated[
        Optional[str],
        typer.Option(
            "--efa",
            "--extra-field-name",
            help=f"The field name to set. Default is '{FIELD_NAME}'.",
            show_default=False,
        ),
    ] = None,
    extra_field_description: Annotated[
        Optional[str],
        typer.Option(
            "--efd",
            "--extra-field-description",
            help=f"The field description to set.",
            show_default=False,
        ),
    ] = None,
    target_entity_id: Annotated[
        Optional[str],
        typer.Option(
            "--ti",
            "--target-id",
            "--target-experiment-id",
            help=f"Obfuscate only the given experiment ID.",
            show_default=False,
        ),
    ] = None,
    target_tag: Annotated[
        Optional[str],
        typer.Option(
            "--tt",
            "--target-tag",
            help=f"Obfuscate only the resources with given tag. "
            f"Both tag and resource ID cannot be passed.",
            show_default=False,
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help=f"Under certain edge-cases, extra fields will "
            f"not be obfuscated without --force.",
            show_default=False,
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=f"When --dry-run is passed, no changes in the server will be applied, "
            f"but target changes will be shown.",
            show_default=True,
        ),
    ] = False,
) -> None:
    with GlobalSharedSession(limited_to="sync"):
        return _obfuscate_entity(
            "experiments",
            extra_field_name,
            extra_field_description,
            target_entity_id,
            target_tag,
            force,
            dry_run,
        )


@app.command("resources", help="Obfuscate all resource titles.")
def obfuscate_resources(
    extra_field_name: Annotated[
        Optional[str],
        typer.Option(
            "--efa",
            "--extra-field-name",
            help=f"The field name to set. Default is '{FIELD_NAME}'.",
            show_default=False,
        ),
    ] = None,
    extra_field_description: Annotated[
        Optional[str],
        typer.Option(
            "--efd",
            "--extra-field-description",
            help=f"The field description to set.",
            show_default=False,
        ),
    ] = None,
    target_entity_id: Annotated[
        Optional[str],
        typer.Option(
            "--ti",
            "--target-id",
            "--target-resource-id",
            help=f"Obfuscate only the given resource ID.",
            show_default=False,
        ),
    ] = None,
    target_tag: Annotated[
        Optional[str],
        typer.Option(
            "--tt",
            "--target-tag",
            help=f"Obfuscate only the resources with given tag. "
            f"Both tag and resource ID cannot be passed.",
            show_default=False,
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help=f"Under certain edge-cases, extra fields will "
            f"not be obfuscated without --force.",
            show_default=False,
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=f"When --dry-run is passed, no changes in the server will be applied, "
            f"but target changes will be shown.",
            show_default=True,
        ),
    ] = False,
) -> None:
    with GlobalSharedSession(limited_to="sync"):
        return _obfuscate_entity(
            "items",
            extra_field_name,
            extra_field_description,
            target_entity_id,
            target_tag,
            force,
            dry_run,
        )


@app.command("revert-experiments", help="Revert obfuscated experiment titles.")
def revert_obfuscated_experiments(
    extra_field_name: Annotated[
        Optional[str],
        typer.Option(
            "--efa",
            "--extra-field-name",
            help=f"The field name to set. Default is '{FIELD_NAME}'.",
            show_default=False,
        ),
    ] = None,
    target_entity_id: Annotated[
        Optional[str],
        typer.Option(
            "--ti",
            "--target-id",
            "--target-experiment-id",
            help=f"Revert only the given experiment ID.",
            show_default=False,
        ),
    ] = None,
    target_tag: Annotated[
        Optional[str],
        typer.Option(
            "--tt",
            "--target-tag",
            help=f"Revert only the experiments with given tag. "
            f"Both tag and experiment ID cannot be passed.",
            show_default=False,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=f"When --dry-run is passed, no changes in the server "
            f"will be applied, but target changes will be shown.",
            show_default=True,
        ),
    ] = False,
) -> None:
    with GlobalSharedSession(limited_to="sync"):
        return _revert_obfuscated_entity(
            "experiments", extra_field_name, target_entity_id, target_tag, dry_run
        )


@app.command("revert-resources", help="Revert obfuscated resource titles.")
def revert_obfuscated_resources(
    extra_field_name: Annotated[
        Optional[str],
        typer.Option(
            "--efa",
            "--extra-field-name",
            help=f"The field name to set. Default is '{FIELD_NAME}'.",
            show_default=False,
        ),
    ] = None,
    target_entity_id: Annotated[
        Optional[str],
        typer.Option(
            "--ti",
            "--target-id",
            "--target-resource-id",
            help=f"Revert only the given resource ID.",
            show_default=False,
        ),
    ] = None,
    target_tag: Annotated[
        Optional[str],
        typer.Option(
            "--tt",
            "--target-tag",
            help=f"Revert only the resources with given tag. "
            f"Both tag and resource ID cannot be passed.",
            show_default=False,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=f"When --dry-run is passed, no changes in the server will be "
            f"applied, but target changes will be shown.",
            show_default=True,
        ),
    ] = False,
) -> None:
    with GlobalSharedSession(limited_to="sync"):
        return _revert_obfuscated_entity(
            "items", extra_field_name, target_entity_id, target_tag, dry_run
        )
