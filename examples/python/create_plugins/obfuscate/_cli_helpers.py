import json
from typing import List, Optional, Literal

from elapi.core_validators import Exit
from elapi.loggers import Logger
from elapi.styles import print_typer_error, stdout_console
from httpx import HTTPError

from .names import (
    FIELD_NAME,
    FIELD_DESCRIPTION,
    DEFAULT_ENTITY_QUERY,
)
from .obfuscate import (
    patch_entity_metadata,
    get_all_entity_data,
    rename_entity_title,
)
from .utils import (
    _is_entity_title_obfuscated,
    _update_extra_fields_with_actual_name,
    _parse_tags,
    _get_entity_endpoint,
)

logger = Logger()


def _obfuscate_entity(
    entity_type: Literal["experiments", "items"],
    extra_field_name: Optional[str] = None,
    extra_field_description: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    target_tag: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    extra_field_name = extra_field_name or FIELD_NAME
    extra_field_description = extra_field_description or FIELD_DESCRIPTION
    if target_entity_id is not None and target_tag is not None:
        print_typer_error(
            f"When --target-{entity_type}-id/--target-id/--ti is given, "
            f"--target-tag is ambiguous. "
            "You can only use either one."
        )
        raise Exit(1)
    try:
        with stdout_console.status(f"Fetching all {entity_type}..."):
            if target_entity_id is not None:
                all_entity_data: List[dict] = [
                    _get_entity_endpoint(entity_type)
                    .get(endpoint_id=target_entity_id, query=DEFAULT_ENTITY_QUERY)
                    .json()
                ]
            else:
                all_entity_data: List[dict] = get_all_entity_data(entity_type)
    except HTTPError as e:
        logger.error(
            f"There was a network error in getting list of all {entity_type}. "
            f"Exception details: {e}"
        )
        raise Exit(1)
    except json.JSONDecodeError as e:
        logger.error(
            f"Unexpected error occurred while decoding list of all {entity_type}."
            f"Exception details: {e}"
        )
        raise Exit(1)
    else:
        for entity in all_entity_data:
            entity_id: int = entity.get("id")
            entity_tags: List[str] = _parse_tags(entity.get("tags", ""))
            if target_tag is not None and target_tag not in entity_tags:
                logger.info(
                    f"{entity_type.capitalize()[:-1]} '{entity_id}' does not have tag '{target_tag}'. "
                    f"{entity_type.capitalize()[:-1]} will be skipped."
                )
                continue
            entity_title: str = entity.get("title")
            entity_metadata: Optional[str] = entity.get("metadata")
            if entity_metadata is not None:
                try:
                    entity_metadata: dict = json.loads(entity_metadata)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        f"{entity_type.capitalize()[:-1]} {entity_id} has metadata, "
                        f"but it is not valid JSON. "
                        f"{entity_type.capitalize()[:-1]} will be skipped."
                    )
                    continue
                else:
                    if not isinstance(entity_metadata, dict):
                        if force is True:
                            logger.warning(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON metadata, "
                                f"but it could not be converted to a dictionary. "
                                f"This is unexpected. {entity_type.capitalize()[:-1]} metadata "
                                f"will be overwritten."
                            )
                            entity_metadata: dict = {}
                        elif entity_metadata == "null":
                            logger.warning(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' has "
                                f"valid JSON metadata: 'null'. "
                                f"{entity_type.capitalize()[:-1]} metadata will be overwritten."
                            )
                            entity_metadata: dict = {}
                        else:
                            logger.warning(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON metadata, "
                                f"but it could not be converted to a dictionary. "
                                f"This is unexpected. Pass '--force' to overwrite metadata like these. "
                                f"{entity_type.capitalize()[:-1]} will bee skipped."
                            )
                            continue
                    extra_fields: dict = entity_metadata.get("extra_fields")
                    if extra_fields is not None:
                        if not isinstance(extra_fields, dict):
                            if force is True:
                                logger.warning(
                                    f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON extra fields, "
                                    f"but it is not a dictionary. "
                                    f"This is unexpected. Pass '--force' to overwrite extra fields like these. "
                                    f"{entity_type.capitalize()[:-1]} will be be overwritten."
                                )
                                extra_fields: dict = {}
                            else:
                                logger.warning(
                                    f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON extra fields, "
                                    f"but it is not a dictionary. "
                                    f"This is unexpected. {entity_type.capitalize()[:-1]} will be skipped."
                                )
                                continue
                        if _is_entity_title_obfuscated(
                            extra_fields, target_field_name=extra_field_name
                        ):
                            logger.warning(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' already has an extra field "
                                f"with name '{extra_field_name}'. "
                                f"{entity_type.capitalize()[:-1]} will be skipped."
                            )
                            continue
                        _update_extra_fields_with_actual_name(
                            extra_fields,
                            field_name=extra_field_name,
                            entity_title=entity_title,
                            field_description=extra_field_description,
                        )
                        entity_metadata.update({"extra_fields": extra_fields})
                        if not dry_run:
                            try:
                                patch_entity_metadata(
                                    entity_type, entity_id, entity_metadata
                                )
                                rename_entity_title(entity_type, entity_id)
                            except HTTPError:
                                continue
                            else:
                                logger.info(
                                    f"{entity_type.capitalize()[:-1]} '{entity_id}' "
                                    f"title '{entity_title}' has been obfuscated."
                                )
                        else:
                            logger.info(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' "
                                f"title '{entity_title}' will be obfuscated."
                            )
                    else:
                        extra_fields: dict = {}
                        _update_extra_fields_with_actual_name(
                            extra_fields,
                            field_name=extra_field_name,
                            entity_title=entity_title,
                            field_description=extra_field_description,
                        )
                        entity_metadata.update({"extra_fields": extra_fields})
                        if not dry_run:
                            try:
                                patch_entity_metadata(
                                    entity_type, entity_id, entity_metadata
                                )
                                rename_entity_title(entity_type, entity_id)
                            except HTTPError:
                                continue
                            else:
                                logger.info(
                                    f"{entity_type.capitalize()[:-1]} '{entity_id}' title "
                                    f"'{entity_title}' has been obfuscated."
                                )
                        else:
                            logger.info(
                                f"{entity_type.capitalize()[:-1]} '{entity_id}' "
                                f"title '{entity_title}' will be obfuscated."
                            )
            else:
                entity_metadata: dict = {}
                extra_fields: dict = {}
                _update_extra_fields_with_actual_name(
                    extra_fields,
                    field_name=extra_field_name,
                    entity_title=entity_title,
                    field_description=extra_field_description,
                )
                entity_metadata.update({"extra_fields": extra_fields})
                if not dry_run:
                    try:
                        patch_entity_metadata(entity_type, entity_id, entity_metadata)
                        rename_entity_title(entity_type, entity_id)
                    except HTTPError:
                        continue
                    else:
                        logger.info(
                            f"{entity_type.capitalize()[:-1]} '{entity_id}' title "
                            f"'{entity_title}' has been obfuscated."
                        )
                else:
                    logger.info(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' title "
                        f"'{entity_title}' will be obfuscated."
                    )


def _revert_obfuscated_entity(
    entity_type: Literal["experiments", "items"],
    extra_field_name: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    target_tag: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    if target_entity_id is not None and target_tag is not None:
        print_typer_error(
            f"When --target-{entity_type}-id/--target-id/--ti is given, "
            f"--target-tag is ambiguous. "
            "You can only use either one."
        )
        raise Exit(1)
    extra_field_name = extra_field_name or FIELD_NAME
    try:
        with stdout_console.status(f"Fetching all {entity_type}..."):
            if target_entity_id is not None:
                all_entity_data: List[dict] = [
                    _get_entity_endpoint(entity_type)
                    .get(endpoint_id=target_entity_id, query=DEFAULT_ENTITY_QUERY)
                    .json()
                ]
            else:
                all_entity_data: List[dict] = get_all_entity_data(entity_type)
    except HTTPError as e:
        logger.error(
            f"There was a network error in getting list of all {entity_type}. "
            f"Exception details: {e}"
        )
        raise Exit(1)
    except json.JSONDecodeError as e:
        logger.error(
            f"Unexpected error occurred while decoding list of all {entity_type}."
            f"Exception details: {e}"
        )
        raise Exit(1)
    else:
        for entity in all_entity_data:
            entity_id: int = entity.get("id")
            entity_tags: List[str] = _parse_tags(entity.get("tags", ""))
            if target_tag is not None and target_tag not in entity_tags:
                logger.info(
                    f"{entity_type.capitalize()[:-1]} '{entity_id}' does not have tag '{target_tag}'. "
                    f"{entity_type.capitalize()[:-1]} will be skipped."
                )
                continue
            _entity_title: str = entity.get("title")
            entity_metadata: str = entity.get("metadata")
            if entity_metadata is None:
                logger.info(
                    f"{entity_type.capitalize()[:-1]} '{entity_id}' has no metadata. "
                    f"{entity_type.capitalize()[:-1]} will be skipped."
                )
                continue
            try:
                entity_metadata: dict = json.loads(entity_metadata)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    f"{entity_type.capitalize()[:-1]} {entity_id} has metadata, "
                    f"but it is not valid JSON. "
                    f"{entity_type.capitalize()[:-1]} will be skipped."
                )
                continue
            else:
                if not isinstance(entity_metadata, dict):
                    logger.warning(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON metadata, "
                        f"but it could not be converted to a dictionary. "
                        f"This is unexpected. "
                        f"{entity_type.capitalize()[:-1]} will be skipped."
                    )
                    continue
                extra_fields: Optional[dict] = entity_metadata.get("extra_fields")
                if extra_fields is None:
                    logger.info(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' has no extra fields. "
                        f"{entity_type.capitalize()[:-1]} will be skipped."
                    )
                    continue
                if not isinstance(extra_fields, dict):
                    logger.warning(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' has valid JSON extra fields, "
                        f"but it is not a dictionary. "
                        f"This is unexpected. "
                        f"{entity_type.capitalize()[:-1]} will be skipped."
                    )
                    continue
                if not _is_entity_title_obfuscated(
                    extra_fields, target_field_name=extra_field_name
                ):
                    logger.info(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' does not have an extra field "
                        f"with name '{extra_field_name}'. "
                        f"{entity_type.capitalize()[:-1]} will be skipped."
                    )
                    continue
                actual_entity_info: dict = extra_fields.pop(extra_field_name)
                actual_entity_title = actual_entity_info["value"]
                if extra_fields:
                    entity_metadata.update({"extra_fields": extra_fields})
                else:
                    entity_metadata.pop("extra_fields")
                if not dry_run:
                    try:
                        rename_entity_title(
                            entity_type, entity_id, new_title=actual_entity_title
                        )
                        patch_entity_metadata(entity_type, entity_id, entity_metadata)
                    except HTTPError:
                        continue
                    else:
                        logger.info(
                            f"{entity_type.capitalize()[:-1]} '{entity_id}' "
                            f"title has been reverted "
                            f"back to its actual title '{actual_entity_title}'."
                        )
                else:
                    logger.info(
                        f"{entity_type.capitalize()[:-1]} '{entity_id}' "
                        f"title will be reverted "
                        f"back to its actual title '{actual_entity_title}'."
                    )
