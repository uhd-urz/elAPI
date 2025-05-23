from typing import Union, List, Optional, Literal

from elapi.api import FixedEndpoint


def _get_entity_endpoint(entity_type: Literal["experiments", "items"], /) -> FixedEndpoint:
    if entity_type == "experiments":
        return FixedEndpoint("experiments")
    elif entity_type == "items":
        return FixedEndpoint("items")
    raise ValueError(f"entity_type {entity_type} is not supported.")


def _is_entity_title_obfuscated(
        extra_fields: dict, *, target_field_name: str
) -> bool:
    if target_field_name in extra_fields:
        return True
    return False


def _update_extra_fields_with_actual_name(
        extra_fields: dict,
        *,
        field_name: str,
        entity_title: str,
        field_description: str,
) -> None:
    extra_fields.update(
        {
            field_name: {
                "type": "text",
                "value": entity_title,
                "readonly": False,
                "description": field_description,
            }
        }
    )


def _parse_tags(entity_tags: Optional[str]) -> Union[List[str], List]:
    if entity_tags is None:
        return []
    return entity_tags.split("|")
