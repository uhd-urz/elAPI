#! /bin/bash

# ╔───────────────────────────────────────╗
# │                                       │
# │    Get list of all resources/items    │
# │    and export them as CSV             │
# │                                       │
# ╚───────────────────────────────────────╝
# -----------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We mainly would like to get familiar with elAPI's raw get, post, patch and delete commands.
# We will start simple by getting a list of all resources/items (previously called "Databases"),
# and export it to a CSV file.

# eLabFTW by default sends resources data in JSON. elAPI attempts to convert the JSON to CSV
# appropriately. CSV can be way more explorable and readable than structured data like JSON.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - We need elAPI installed (preferably via pipx for this example).

elapi get items --format csv --export ./Downloads
# 1. elAPI get items makes a GET request to endpoint "items".
# 2. --format defines the data format we want to have the resources as: CSV
# 3. --export defines the location. The location can be a file path or a directory.
# Here, we pass a directory "<current directory>/Downloads".
# --export will automatically set an appropriate file name for us.
