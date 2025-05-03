# ╔─────────────────────────────────╗
# │                                 │
# │    Create a new user account    │
# │    in batch (Advanced)          │
# │                                 │
# ╚─────────────────────────────────╝
# -----------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# This is the final script where we combine everything we have done.
# We will create new users in batch. The user data is stored in a CSV file.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - User data in a CSV file: user_data.csv.
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
# 1. We do not create any new function as we already have what we need. We start from
# 'if __name__ == "__main__"' block.
# 2. We read/parse user information from user_data.csv.
# 3. We loop over each user account information, and we call
# "create_user_advanced" and "create_user_password".
from pathlib import Path

# For reusing the functions we have already created
from create_new_user_advanced import (
    users_endpoint,
    validate,
    create_user_advanced,
)
from create_new_user_with_password_advanced import create_user_password

if __name__ == "__main__":
    import random  # We need to generate a random fake middle name
    import string
    import uuid  # We need to generate a random password
    import csv  # to parse CSV file with user data
    from elapi.styles import stdout_console  # For printing pretty text formatting

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
    with stdout_console.status("[bold]Validating...[/bold]\n"):
        # status method will show an animated spinner.
        validate()
    stdout_console.print("[bold green]Validation complete.[/bold green]")
    stdout_console.print("\n")
    # +-------------------------------------------+
    # |  Read user information from the CSV file  |
    # +-------------------------------------------+
    with open(Path(__file__).parent / "user_data.csv", "r") as f:
        user_data = list(csv.DictReader(f, delimiter=","))

    # Iterate over each user information
    for user in user_data:
        # +----------------------------+
        # |  Create each user in loop  |
        # +----------------------------+
        firstname = f"{user['first_name']} {middle_name}"
        lastname = user["last_name"]
        email = f"{middle_name}_{user['email']}"
        # We add random middle name to email to keep our email address unique.
        # eLabFTW will not allow duplicate email addresses to be created!
        # In real life use case, adding middle name is not necessary!
        team_id = user["team_id"]
        valid_until = user["valid_until"]
        # Try adding valid_until by yourself!
        # Hint: Start with adding a new parameter called "valid_until" to create_user_advanced function.
        new_user_id = create_user_advanced(
            firstname=firstname,
            lastname=lastname,
            email=email,
            team_id=team_id,
        )

        # +---------------------------------------------+
        # |  Assign password to the newly created user  |
        # +---------------------------------------------+
        # First, we generate a random password from UUID.
        password = uuid.uuid4().hex[0:13]
        # First, 13 characters of UUID. eLabFTW requires at least a 12-digit password.
        create_user_password(user_id=new_user_id, new_password=password)
        print(
            "───────────────────────────────────────────────────────────────────────────────────────────────────────"
        )

    stdout_console.print(
        "[bold green]All user accounts are created successfully.[/bold green]"
    )
    # We have to close the session(s) manually.
    users_endpoint.close()
