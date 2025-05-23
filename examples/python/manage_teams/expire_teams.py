# ╔─────────────────────────────────────╗
# │                                     │
# │    Expire members in a team         │
# │                                     │
# ╚─────────────────────────────────────╝
# ---------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We will expire members of a team.
# We are expiring the team likely because the members have left the project/institution.
# This script assumes the members do not belong to more than one team.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `pip install elapi` should work.
# Note: The elAPI we installed using `uv tool` or pipx remains isolated and is meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. The operation can be DESTRUCTIVE, so first we validate hosts to make sure that we are
# running the script against development servers, and not against the production server.
# 2. We get a list of all user data
# 3. We iterate over each user data and check if the user "teams" field contains the target team ID
# we want to expire. If it does, that indicates the user does belong to the target team.
# 4. We PATCH the user with the new expiry date

import asyncio

from elapi.api import PATCHRequest, GlobalSharedSession
from elapi.loggers import Logger
from elapi.plugins.commons import RecursiveInformation
# commons is a plugin with some helpful CLI functions, but commons plugin itself does not come with a CLI
from elapi.validators import Validate, PermissionValidator, HostIdentityValidator

logger = Logger()  # Handles logging to elAPI log file and to STDERR

validate = Validate(
    HostIdentityValidator(
        restrict_to=[
            "https://elabftw-dev.uni-heidelberg.de/api/v2",  # Heidelberg University run development servers
            "https://elabftw-dev-002.uni-heidelberg.de/api/v2",  # Replace the server addresses with your own
        ]
    ),  # restrict_to makes sure your host is either of the dev instances and not the production instance.
    # restrict_to can be removed once testing is done.
    PermissionValidator("sysadmin"),
    # Makes sure you have eLabFTW "sysadmin" permission
)
validate()

with GlobalSharedSession():
    patch = PATCHRequest()  # the connection is not open yet!
    TARGET_TEAM_ID = "95"  # ID of the team to expire.
    EXPIRY_DATE = "3001-01-01"  # the new expiry date to set for target users.
    try:
        users_information = asyncio.run(
            RecursiveInformation(
                endpoint_name="users", endpoint_id_key_name="userid"
            ).items()  # verbose=False will disable the progress bar
            # RecursiveInformation().items() method asynchronously fetches a list of dictionaries,
            # where each dictionary correspondents to a single user data.
        )
    except (RuntimeError, InterruptedError) as e:
        raise InterruptedError(
            "Getting users data was not successful."
        ) from e  # elAPI handles most of the cleanup already.

    for user in users_information:
        if len(user["teams"]) > 1:
            # user["teams"] is again a list of dictionaries of teams the user belongs to
            # logger.warning(
            #     f"The user with user ID {user['userid']} belongs to more than one team! "
            #     f"This user will be skipped and not be expired."
            # )
            continue
        if str(user["teams"][0]["id"]) == TARGET_TEAM_ID:
            # Each user should only belong to a single team.
            patch(
                endpoint_name="users",
                endpoint_id=user["userid"],
                data={"valid_until": EXPIRY_DATE},
            )  # the connection opens here
            logger.info(
                f"An expiration date for the user with user ID {user['userid']} has been successfully set."
            )
