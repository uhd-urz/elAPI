# ╔─────────────────────────────────────────────╗
# │                                             │
# │    Attach file to an existing experiment    │
# │    by Unique eLabID and with validation     │
# │                                             │
# ╚─────────────────────────────────────────────╝
# -----------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We attach a local file to an experiment same as before as we did in "add_attachment_simple.py".
# We will do some additional validations before uploading the attachment.
# Furthermore, instead of using the experiment ID, we will use the "Unique eLabID,"
# which is more conspicuous on an experiment page.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - We only attach to an experiment that already exists in eLabFTW.
# - We get the path of the local file for attachment. Here, we already have two
# example files stored in ./Attachments directory.
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `pip install elapi` should work.
# Note: The elAPI we installed through pipx remains isolated, only meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. elAPI already offers a plugin for working with eLabFTW experiments.
# We use "attach_to_experiment" method provided by the "experiments" plugin.
# 2. We define the ID for the existing experiment we want to attach our file to.
# 3. We define the path to our attachment file.
# 4. We call "attach_to_experiment".
# 5. We print a minimal success message.
from pathlib import Path

from httpx import HTTPError

from elapi.loggers import Logger
from elapi.plugins.experiments import attach_to_experiment, ExperimentIDValidator
# For making sure we have the appropriate permission
from elapi.validators import (
    Validate,
    HostIdentityValidator,
    APITokenRWValidator,
    ValidationError,
    Exit,
)

# We use Logger instance for logging errors and other messages
# Logs are printed to the terminal and to a local file.
# See the log file location from `elapi show-config`.
logger = Logger()

# We need an API key/token with write permission to be able to upload an attachment.
# We also need to make sure we have the right permission(s) to be able to create users in the first place.
# These validations can be immensely helpful as they can help us understand any
# permission or network related error early on without having to analyze the error response sent by eLabFTW.
validate = Validate(HostIdentityValidator(), APITokenRWValidator(can_write=True))
# HostIdentityValidator mainly ensures if the configured host and api_token are valid.
# APITokenRWValidator makes sure our API key/token has write permission.
# If something is found to be wrong (or invalid) by the validator, elAPI will show the appropriate error message
# and quit.
# +------------------+
# |  Run validation  |
# +------------------+
validate()

UNIQUE_ELAB_ID = "20240309-b629ba4a6789fac1662505d057a3c57459ccc646"
# Unique eLabID instead of experiment ID of our experiment
ATTACHMENT_FILE = Path(__file__).parent / "Attachments/elapi_get_architecture_old.pdf"
# +-------------------------------+
# |  Run validation for           |
# |  experiment ID/unique eLabID  |
# +-------------------------------+
# We validate the unique eLabID, i.e., we want to check if the experiment exists first.
try:
    experiment_id = Validate(ExperimentIDValidator(UNIQUE_ELAB_ID)).get()
except ValidationError as e:
    logger.error(e)
    # If the ID/experiment does not exist, we abort/quit.
    raise Exit(1)
try:
    # If ID does exist, we continue with uploading the attachment.
    attach_to_experiment(
        experiment_id=experiment_id,
        file_path=ATTACHMENT_FILE,
        comment="Uploaded via elAPI",
    )
    # We catch any network error during upload.
except HTTPError as e:
    logger.error(
        f"There was a network error in attaching the file '{ATTACHMENT_FILE}'. "
        f"Exception details: {e}"
    )
    raise Exit(1)
else:
    # If everything goes well (no error caught above),
    # we print a success message.
    logger.info(f"Successfully attached the file '{ATTACHMENT_FILE}' to experiment.")
