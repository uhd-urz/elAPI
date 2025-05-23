import json
from typing import Union, List, Optional, Literal

from elapi.loggers import Logger
from httpx import HTTPError

from .names import (
    ENTITY_METADATA_KEY,
    DEFAULT_ENTITY_QUERY,
)
from .utils import _get_entity_endpoint

logger = Logger()


def patch_entity_metadata(
        entity_type: Literal["experiments", "items"], entity_id: Union[str, int], entity_metadata: dict
) -> None:
    if entity_metadata != "null":
        if not isinstance(entity_metadata, dict):
            raise TypeError("entity_metadata must be a dictionary or 'null'!")
        if entity_metadata.get(ENTITY_METADATA_KEY):
            raise ValueError("entity_metadata must be without the key 'metadata'.")
    entity_metadata: dict = {
        ENTITY_METADATA_KEY: json.dumps(entity_metadata)
    }
    response = _get_entity_endpoint(entity_type).patch(entity_id, data=entity_metadata)
    if not response.is_success:
        main_message = f"Modifying metadata for {entity_type} '{entity_id}' failed"
        logger.error(
            f"{main_message}. "
            f"Response HTTP code: {response.status_code}. "
            f"Response: {response.text}"
        )
        exception = HTTPError(f"{main_message}.")
        exception.response = response
        raise exception


def get_all_entity_data(entity_type: Literal["experiments", "items"]) -> List[dict]:
    entity_endpoint = _get_entity_endpoint(entity_type)
    all_entity_data = entity_endpoint.get(
        endpoint_id=None, query=DEFAULT_ENTITY_QUERY
    ).json()
    expected_limit = offset = len(all_entity_data)
    while (
            len(
                continuous_batch := entity_endpoint.get(
                    endpoint_id=None,
                    query={"offset": offset, **DEFAULT_ENTITY_QUERY},
                ).json()
            )
            != 0
    ):
        all_entity_data.extend(continuous_batch)
        offset += expected_limit
    return all_entity_data


def rename_entity_title(
        entity_type: Literal["experiments", "items"], entity_id: Union[str, int], new_title: Optional[str] = None
) -> None:
    new_title = new_title or str(entity_id)
    response = _get_entity_endpoint(entity_type).patch(entity_id, data={"title": new_title})
    if not response.is_success:
        main_message = f"Modifying title for {entity_type} '{entity_id}' failed"
        logger.error(
            f"{main_message}. "
            f"Response HTTP code: {response.status_code}. "
            f"Response: {response.text}"
        )
        exception = HTTPError(f"{main_message}.")
        exception.response = response
        raise exception
