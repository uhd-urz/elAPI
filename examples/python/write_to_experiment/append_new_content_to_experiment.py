# ╔─────────────────────────────────────────────╗
# │                                             │
# │    Append (or add) new text to an           │
# │    experiment                               │
# │                                             │
# ╚─────────────────────────────────────────────╝
# -----------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# Given an experiment ID or a unique eLabID and an attachment ID, we would like
# to update the experiment body with new text/information.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `uv add elapi` or `pip install elapi` will work.
# Note: The elAPI we installed through pipx remains isolated, meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# We define append_to_experiment that accepts an experiment ID or unique eLabID
# We validate the experiment ID/unique eLabID
# We store the existing experiment body
# We send a PATCH request with existing experiment body + new content

from typing import Union, Optional

from elapi.api import FixedEndpoint
from elapi.core_validators import Exit
from elapi.loggers import Logger
from elapi.plugins.experiments import ExperimentIDValidator
from elapi.validators import Validate, HostIdentityValidator, ValidationError

logger = Logger()


def append_to_experiment(
    experiment_id: Union[str, int],
    content: str,
) -> None:
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
    # The experiment body is stored in "body" in the response data.
    # We want to make sure first, we don't overwrite the existing experiment body.
    current_body: Optional[str] = session.get(experiment_id).json()["body"]
    if current_body is None:
        current_body: str = ""
    # The PATCH request is sent with the stored existing
    # body content and the new content
    session.patch(
        experiment_id,
        data={"body": current_body + content},
    )
    session.close()


if __name__ == "__main__":
    append_to_experiment(experiment_id=147, content="Aspirin doesn't cure Covid-19.")
