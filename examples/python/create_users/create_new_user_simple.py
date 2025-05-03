# ╔───────────────────────────────────────────╗
# │                                           │
# │    Create a new user account in Python    │
# │                                           │
# ╚───────────────────────────────────────────╝
# ---------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We would like to create a new eLabFTW user account with elAPI as a library in Python.
# elAPI is designed to work both as a CLI tool and a library.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `pip install elapi` should work.
# Note: The elAPI we installed through pipx remains isolated, it is only meant to work as
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
# 1. We define our function "create_user_simple" which when called will create a new user.
# 2. We use POSTRequest class from elAPI to make a POST request to eLabFTW server.
# 3. We print a success or error message.
# 4. We call the function from under 'if __name__ == "__main__"' block.

# For making POST request to eLabFTW
from elapi.api import POSTRequest


def create_user_simple(firstname: str, lastname: str, email: str, team_id: int) -> None:
    # We make a POST request with the user information
    # API documentation: https://doc.elabftw.net/api/v2/#/Users/post-user
    post_session = POSTRequest()
    # POSTRequest will automatically close the session once a request has been made.
    new_user_request = post_session(
        endpoint_name="users",  # Our target endpoint name
        data={
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "team": team_id,
            "usergroup": 4,  # usergroup refers to the permission group, i.e., whether
            # we want the user to be a sysadmin (1), admin (2), or user (4).
        },
    )
    # We print a success message for successful account creation, or
    # an error message in the case of an error. This is a simple STDOUT print.
    # In the advanced implementation, we will print to STDERR.
    if new_user_request.is_success:
        print(f"User with '{firstname} {lastname} <{email}>' successfully created. ")
    else:
        print(
            f"An error occurred! User with '{firstname} {lastname} <{email}>' could not be created! "
        )


if __name__ == "__main__":
    import random

    unique_identifier = random.randint(500, 5000)
    # any random integer between 500 and 5000
    # eLabFTW will not allow duplicate email addresses. Since we are creating fake user
    # accounts, we use the random number as an identifier to make each
    # email address username unique.
    create_user_simple(
        "Max",
        f"Mustermann {unique_identifier}",
        email=f"max.mustermann{unique_identifier}@localhost.example",
        team_id=2,  # Team name "team alpha" in elabftw-dev
    )
