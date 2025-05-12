# ╔───────────────────────────────────╗
# │                                   │
# │    Create a new user account      │
# │    with validations (Advanced)    │
# │                                   │
# ╚───────────────────────────────────╝
# -------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We created a user account in a simple way in create_new_user_simple.py.
# In this script, we will do the same again but with some frequently necessary validations
# that our earlier script is missing:
# 1. Validating the provided host URL and API key/token
# 2. Validating network connection
# 3. Validating if we have sufficient permission to create a user account in the first place
# These validations can be crucial in catching early mistakes. For example, as we are experimenting
# with the automation of creating new user accounts, we would like to make sure we are targeting
# our development server and not our production server. But we could have given the production host
# URL to the configuration file elapi.yml by mistake. We can use one of the validators
# to guarantee that we are warned and stopped if we are accidentally targeting the wrong server.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `pip install elapi` should work.
# Note: The elAPI we installed using `uv tool` or pipx remains isolated and is meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# - We need the following minimum user information to create an account:
# 1. First name, 2. Last name, 3. Email, 4. Team ID
# A user always belongs to a team, hence the team ID. If no team ID is provided,
# eLabFTW will assign the user to the "Default Team".
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. We define the validations we want to perform before making any actual request.
# as listed in "Objective" section.
# 3. We define our function "create_user_advanced" which when called will create a new user.
# 2. We use FixedEndpoint class to make a POST request now and later a PATCH request.
# 3. We log every success or error message instead of just printing it.
# 4. We call the function from under 'if __name__ == "__main__"' block.


# For type hints only. This is optional
from typing import Union

# For handling HTTP connections
from elapi.api import FixedEndpoint
# For logging
from elapi.loggers import Logger
# For reading HTTP response headers sent by eLabFTW
from elapi.plugins.commons import get_location_from_headers
# For terminating the program
from elapi.validators import Exit
# For making sure we have the appropriate permission
from elapi.validators import (
    Validate,
    HostIdentityValidator,
    APITokenRWValidator,
    PermissionValidator,
)

# We want a simple way to make repeated get, post, patch, delete requests to a single endpoint.
# In this case, we want to create and modify the "users" endpoint,
# to create a user and then modify its account.
# For that, we imported the "FixedEndpoint" class.
# A FixedEndpoint instance targets one endpoint only.
# It makes it convenient to handle the get/post/patch/delete sessions for that endpoint.
# A FixedEndpoint instance needs to be manually closed with FixedEndpoint().close()

# First we create a FixedEndpoint instance with the endpoint of our interest "users" as its only argument.
users_endpoint = FixedEndpoint("users")

# We use Logger instance for logging errors and other messages
# Logs are printed to the terminal and to a local file.
# See the log file location from `elapi show-config`.
logger = Logger()

# We need to make sure we have the right permission(s) to be able to create users in the first place.
# These validations can be immensely helpful as they can help us understand any
# permission or network related error early on without having to analyze the error response sent by eLabFTW.
validate = Validate(
    HostIdentityValidator(  # HostIdentityValidator mainly ensures if the configured host and api_token are valid.
        restrict_to=[
            "https://elabftw-dev.uni-heidelberg.de/api/v2",  # Make sure every character match as it is on elapi.yml!
            "https://elabftw-dev-002.uni-heidelberg.de/api/v2",
        ]
    ),  # Important: We want to target either one of the dev instances and avoid writing on the production instance!
    # We can do that with restrict to.
    # This is merely a validation. Requests are sent to the "host" found in the elAPI configuration file: elapi.yml
    # Run "elapi show-config" to see which host elAPI will send requests to.
    # restrict_to can be removed once testing is done.
    APITokenRWValidator(
        can_write=True
    ),  # We want to make sure our API key/token has write permission.
    PermissionValidator(
        "sysadmin"
    ),  # Only sysadmins can create users. We want to make sure we are sysadmins.
)


# If something is found to be wrong (or invalid) by the validator, elAPI will show appropriate error message
# and quit.

# Let's start with a creating a single user the simplest way
# We need the following information to create one:
# 1. First name, 2. Last name, 3. Email, 4. Team ID
# A user always belongs to a team, hence the team ID. If no team ID is provided,
# eLabFTW will assign the user to the "Default Team".


def create_user_advanced(
    firstname: str, lastname: str, email: str, team_id: Union[int, str]
) -> str:
    # We make a POST request with the user information
    # API documentation: https://doc.elabftw.net/api/v2/#/Users/post-user
    new_user = users_endpoint.post(
        data={
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "team": team_id,
            "usergroup": 4,  # usergroup refers to the permission group, i.e., whether
            # we want the user to be a sysadmin (1), admin (2), or user (4).
        }
    )
    if not new_user.is_success:
        # We want to show and log an error if the user could not have been created.
        logger.error(
            f"User with '{firstname} {lastname} <{email}>' couldn't be created!"
            f"Received response: '{new_user.content}'"
        )
        raise Exit(1)  # We quit with shell exit code 1.
        # Exit makes sure not to quit Python when we're inside the Python REPL!

    # The above post request will immediately create the user.
    # We also want the user ID that was just created, so we can modify the user's account later.
    # E.g., if we wanted to add a new password to the user. Note: By default, eLabFTW doesn't assign
    # a new password to a user's account when created via the API.
    new_user_header = new_user.headers
    user_id, user_url = get_location_from_headers(new_user_header)
    # Finally, we show a success message.
    logger.info(
        f"User with '{firstname} {lastname} <{email}>' successfully created. "
        f"New user ID: '{user_id}',\n"
        f"URL: {user_url}."
    )
    return user_id  # We return the newly created user ID that can be used later.


if __name__ == "__main__":
    import random  # We need to generate a random fake middle name
    import string

    # +-----------------------------+
    # |  Generate fake middle name  |
    # +-----------------------------+
    # This step is needed for this demo only.
    # We add random middle name to email to keep our email address unique.
    # eLabFTW will not allow duplicate email addresses to be created!
    # In real life use case, adding middle name is not necessary!
    middle_name = "".join(
        random.sample(string.ascii_lowercase, random.randint(6, 10))
    ).capitalize()

    # +------------------+
    # |  Run validation  |
    # +------------------+
    # We still haven't run the validation yet.
    # First, run validation by just calling the "validate" instance.
    validate()

    # +-----------------------------------------+
    # |  Finally, call function to create user  |
    # +-----------------------------------------+
    new_user_id = create_user_advanced(
        firstname=f"Max {middle_name}",
        lastname="Mustermann",
        email=f"max_{middle_name.lower()}.mustermann@localhost.example",
        team_id=2,  # Team name "team alpha" in elabftw-dev
    )

    # We have to close the session(s) manually.
    users_endpoint.close()
