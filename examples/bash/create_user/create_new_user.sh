#! /bin/bash
# ╔─────────────────────────────────────────╗
# │                                         │
# │    Create a new user account in Bash    │
# │                                         │
# ╚─────────────────────────────────────────╝
#--------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We would like to create a new eLabFTW user account. We will also pass some
# optional parameter to the API call.
#
# Ideally, this can be done with a single line (see comment line below starting with *)
# of elapi command via the terminal. Here, we show the example in Bash to demonstrate
# how simple automation for eLabFTW can be done, and to show how creating a single user account
# in the simplest way looks like. In the next example, we will show
# how to create a new user account in Python.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - We need elAPI installed (preferably via pipx for this example).
# - In case, we don't have bash in our system, we can follow an equivalent solution
# that just uses elAPI directly on the CLI (comment line below starting with *).
# - We need the following minimum user information to create an account:
# 1. First name, 2. Last name, 3. Email, 4. Team ID
# A user always belongs to a team, hence the team ID. If no team ID is provided,
# eLabFTW will assign the user to the "Default Team".

RANDOM_NUM="$RANDOM"              # Random number for creating unique user name/email.
FIRSTNAME="Max"                   # User first name
LASTNAME="Mustermann $RANDOM_NUM" # User lastname name
EMAIL="max.mustermann$RANDOM_NUM@localhost.example"
TEAM_ID=2                # Which team the user should belong to. Team name "team alpha" in elabftw-dev
VALID_UNTIL="2024-12-31" # When the user account should expire
# * The following is equivalent of:
# elapi post users -d '{"firstname": <name>, "lastname": <name>, "email": <email>, "team": <team ID>, "valid_until": <date>}'
elapi post users -d "{\"firstname\": \"$FIRSTNAME\", \"lastname\": \"$LASTNAME\", \"email\": \"$EMAIL\",
\"team\": \"$TEAM_ID\", \"valid_until\": \"$VALID_UNTIL\"}"
# Note: No password is assigned yet.
