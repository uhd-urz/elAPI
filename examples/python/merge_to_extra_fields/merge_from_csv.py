# ╔──────────────────────────────────╗
# │                                  │
# │                                  │
# │  Merge new data to extra fields  │
# │                                  │
# │                                  │
# ╚──────────────────────────────────╝
# -----------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# Given an experiment ID or a resource ID, we would like to update its extra fields data with
# new data parsed from a CSV file by merging to the extra fields instead of overwriting it.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.11. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `uv add elapi` or `pip install elapi` will work.
# Note: The elAPI we installed using `uv tool` remains isolated from the project and is meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Data overview  │
# └─────────────────┘
# A data.csv file comes with this example. The header of this CSV is expected to match the extra
# metadata schema we want to target. In this case, we want to create or merge a
# field of type "Number". On the eLabFTW browser GUI, a "Number" field has
# a name, a unit, description and value. The JSON field looks like:
# "<name>": {
#     "type": "number",
#     "unit": "<value from the "unit" column>",
#     "units": [<value from the "unit" column>],
#     "value": "<value from the "value" column>",
#     "description": "<Any description>",
#     }
# Note: The "name" has to be unique in extra metadata.
# The CSV header column names match the JSON field names: name, unit, value
# We ignore description for now.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# - We convert the CSV file to an extra-metadata-valid dictionary in parse_user_csv_data
# - We define merge_to_extra_metadata that accepts an experiment ID or unique eLabID
# - We validate the experiment ID/unique eLabID
# - We first check if a given field from data.csv already exists in the extra fields and
# inform the user if so
# - We merge the CSV data to extra fields
import csv

import json
from elapi.api import FixedEndpoint
from elapi.core_validators import Exit
from elapi.loggers import Logger
from elapi.plugins.experiments import ExperimentIDValidator
from elapi.validators import Validate, HostIdentityValidator, ValidationError
from pathlib import Path

logger = Logger()


def parse_user_csv_data(csv_path: Path, csv_delimiter: str = ",") -> dict[str, dict]:
    valid_metadata: dict[str, dict] = {}
    with csv_path.open(mode="r", encoding="utf-8") as f:
        # Convert file data to a CSV object
        csv_data = csv.DictReader(f, delimiter=csv_delimiter)
        for resource in csv_data:
            # Here, we create a dictionary that matches the schema of the target extra field.
            # E.g., "Coffee": {
            #   "type": "number",
            #   "unit": "oz",
            #   "units": ["oz", "liter"],
            #   "value": "10",
            #   "description": "Got caffeine?",
            #   }
            valid_metadata[resource.pop("name")] = resource
    return valid_metadata


def merge_to_extra_metadata(experiment_id: str | int, user_metadata: dict[str, dict]):
    # We always need to make sure we are targeting the correct server with no foreseeable network issues.
    # I.e., our API key/token is correct, the host address is valid, etc.
    # If something is found to be wrong (or invalid) by the validator, elAPI will show the appropriate error message
    # and quit.
    validate_config = Validate(HostIdentityValidator())
    validate_config()

    try:
        # ExperimentIDValidator checks first if the experiment ID exists.
        # If a unique eLabID is given, the corresponding experiment ID is returned with
        # get() method.
        experiment_id = Validate(ExperimentIDValidator(experiment_id)).get()
    except ValidationError as e:
        logger.error(e)
        raise Exit(1)

    # There is also a shortcut "FixedExperimentEndpoint" that can be imported from elapi.plugins.experiments
    session = FixedEndpoint("experiments")
    # We store the metadata from the API. This response is in string, so we need to convert it
    # back to Python dictioary with json.load
    metadata = json.loads(
        session.get(endpoint_id=experiment_id).json().get("metadata", "{}")
    )
    # We want to check if a targe field name already exists. If so, we inform the user with
    # a log message.
    extra_fields: dict[str, dict] = metadata.get("extra_fields", {})
    for resource_name in user_metadata:
        if resource_name in extra_fields.keys():
            logger.info(
                f"Resource '{resource_name}' already exists in the extra metadata. "
                f"So its value will be updated."
            )
        else:
            logger.info(
                f"Resource '{resource_name}' does not exists in the extra metadata yet. "
                f"So a new field will be created with the provided value."
            )
            user_metadata[resource_name].update(
                {"type": "number", "units": [user_metadata[resource_name]["unit"]]}
            )
    # Finally, we dump the data into "extra_fields". Note, the "metadatamerge" in data is
    # what requesting a merge as opposed to "metadata" which would request an overwrite.
    p = session.patch(
        endpoint_id=232,
        data={"metadatamerge": json.dumps({"extra_fields": {**user_metadata}})},
    )
    if p.is_success:
        logger.info("Extra fields merge is successful.")
    else:
        logger.error("Extra fields merge failed.")
        raise Exit(1)


if __name__ == "__main__":
    # First, we convert the user-given extra fields data from the CSV file to API
    # extra-metdata-compatible Python dictionary
    new_user_data = parse_user_csv_data(Path(f"{__file__}").parent / "data.csv")
    # Then we pass that to merge_to_extra_metadata
    merge_to_extra_metadata(experiment_id=232, user_metadata=new_user_data)
