# ╔───────────────────────────────────────────╗
# │                                           │
# │    Create a new user account              │
# │    with password assignment (advanced)    │
# │                                           │
# ╚───────────────────────────────────────────╝
# ---------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We have created a user account, but no password has been assigned to it yet.
# The user themselves can request a password reset, or we can assign a password for them.
# This can be helpful if we are setting up accounts on behalf of our eLabFTW users,
# and we want to provide them with an initial password.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `pip install elapi` should work.
# Note: The elAPI we installed through pipx remains isolated, only meant to work as
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
# 1. We call "create_new_user_advanced" from the "create_new_user_advanced.py" to create the account.
# 2. We define create_user_password function that assigns a new password.
# 3. We use FixedEndpoint instance from the earlier script to make a PATCH request to add new password.
# 4. We log every success or error message.
# 5. We call the function "create_user_password" from under 'if __name__ == "__main__"' block.

# For reusing the functions we have already created
from create_new_user_advanced import (
    users_endpoint,
    logger,
    validate,
    create_user_advanced,
)

# For terminating the program
from elapi.validators import Exit


def create_user_password(user_id: str, new_password: str) -> None:
    request = users_endpoint.patch(
        endpoint_id=user_id, data={"action": "updatepassword", "password": new_password}
    )
    if not request.is_success:
        # We want to show and log an error if the user could not have been created.
        logger.error(f"Password for user with ID '{user_id}' couldn't be created!")
        raise Exit(1)  # We quit with shell exit code 1.
        # Exit makes sure not to quit Python when we're inside the Python REPL!
    logger.info(f"Password successfully created for user with ID {user_id}.")


if __name__ == "__main__":
    import random  # We need to generate a random fake middle name
    import string
    import uuid  # We need to generate a random password

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

    # +-----------------------------------------------+
    # |  Create user by calling create_user_advanced  |
    # +-----------------------------------------------+
    new_user_id = create_user_advanced(
        firstname=f"Max {middle_name}",
        lastname="Mustermann",
        email=f"max_{middle_name.lower()}.mustermann@localhost.example",
        team_id=2,  # Team name "team alpha" in elabftw-dev
    )

    # +---------------------------------------------+
    # |  Assign password to the newly created user  |
    # +---------------------------------------------+
    # First, we generate a random password from UUID.
    password = uuid.uuid4().hex[0:13]
    # First, 13 characters of UUID. eLabFTW requires at least a 12-digit password.
    create_user_password(user_id=new_user_id, new_password=password)

    # We have to close the session(s) manually.
    users_endpoint.close()
