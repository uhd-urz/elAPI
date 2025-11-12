import json
import re
from collections import defaultdict
from typing import Any

import httpx
import yaml
from httpx import HTTPError

from .._names import ELAB_BRAND_NAME
from ..loggers import Logger
from ..utils import OpenAPISpecificationException
from ._names import ElabVersionDefaults

logger = Logger()


def read_openapi_spec(url: str) -> dict[str, Any]:
    try:
        spec = httpx.get(url)
    except HTTPError as e:
        raise OpenAPISpecificationException(
            f"{ELAB_BRAND_NAME} OpenAPI specification URL could not be fetched. "
            f"Exception details: {e}"
        ) from e
    else:
        try:
            spec_yaml = yaml.safe_load(spec.text)
        except yaml.YAMLError as e:
            raise OpenAPISpecificationException(
                f"{ELAB_BRAND_NAME} OpenAPI specification could not parsed "
                f"as a valid YAML. Exception details: {e}"
            ) from e
        else:
            return spec_yaml


def parse_openapi_spec(spec: dict[str, Any]) -> dict[str, list[str]]:
    endpoints: dict[str, set[str]] = defaultdict(set)
    try:
        spec_paths = spec["paths"]
    except KeyError as e:
        raise OpenAPISpecificationException(
            "The OpenAPI specification does not contain the 'paths' field! "
        ) from e
    for path in spec_paths:
        endpoints_pattern = re.compile(r"^/([{}\w\-]+)(/{id}/([\w\-]+)(/{subid})?)?")
        if match := endpoints_pattern.match(path):
            main_endpoint_name, sub_endpoint_name = match.group(1, 3)
            match main_endpoint_name:
                case "{entity_type}":
                    try:
                        for parameter in spec_paths[path]["parameters"]:
                            match parameter["name"]:
                                case "entity_type":
                                    entities = parameter["schema"]["enum"]
                                    for entity in entities:
                                        match sub_endpoint_name:
                                            case None:
                                                endpoints[entity] = set()
                                            case _:
                                                endpoints[entity].add(sub_endpoint_name)
                                    break
                                case _:
                                    continue
                    except KeyError as e:
                        raise OpenAPISpecificationException(
                            f"'entity_type' parameter is found in the OpenAPI specification "
                            f"path '{path}' but other expected field names were not found!"
                        ) from e
                case _:
                    match sub_endpoint_name:
                        case None:
                            endpoints[main_endpoint_name] = set()
                        case _:
                            endpoints[main_endpoint_name].add(sub_endpoint_name)
        else:
            raise OpenAPISpecificationException(
                f"The OpenAPI specification path '{path}' does not match "
                f"the expected pattern. This likely means a new type of endpoint "
                f"path has been added to the specification that needs to be "
                f"re-considered.."
            )
    return {k: sorted(list(v)) for k, v in sorted(endpoints.items())}


if __name__ == "__main__":
    versions_dir = ElabVersionDefaults.versions_dir
    for version in ElabVersionDefaults.supported_versions:
        version_file = versions_dir / f"{version}.{ElabVersionDefaults.file_ext}"
        if version_file.exists():
            logger.info(f"Version '{version}' already exists in {versions_dir}.")
            continue
        loaded_spec = read_openapi_spec(
            f"https://raw.githubusercontent.com/elabftw/elabftw/refs/tags/{version}/apidoc/v2/openapi.yaml"
        )
        version_file.write_text(
            json.dumps(parse_openapi_spec(loaded_spec), indent=4), encoding="utf-8"
        )
        logger.info(f"Version '{version}' data has been stored in {versions_dir}.")
