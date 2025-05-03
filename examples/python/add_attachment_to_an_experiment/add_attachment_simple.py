# ╔─────────────────────────────────────────────╗
# │                                             │
# │    Attach file to an existing experiment    │
# │                                             │
# ╚─────────────────────────────────────────────╝
# --------------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# eLabFTW browser GUI provides a great interface for attaching local files to an experiment.
# Sometimes we have more than just a single file; the file could be machine generated, e.g.,
# we could benefit from a workflow where images captured by say a
# laboratory compound microscope are automatically attached to a target experiment.
# The API would be the way to accomplish such automated workflows.
# We will implement a simple version of that here.
# We will attach a local file to an existing experiment via the API.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - For now, we only attach to an experiment that already exists in eLabFTW.
# - We of course get the path of the local file for attachment. Here, we already have two
# example files stored in ./attachments directory.
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

# "experiments" plugin: For attaching to experiment
from elapi.plugins.experiments import attach_to_experiment

# We can just use the elapi experiments plugin that already
# offers a method to attach a file to an existing experiment.
EXPERIMENT_ID = 129
ATTACHMENT_FILE = Path(__file__).parent / "attachments/ChemischeElemente_Beispiel.csv"
attach_to_experiment(
    experiment_id=129,
    file_path=ATTACHMENT_FILE,
    attachment_name="ChemistryElements_example.csv",
    # We can pass an attachment name that can be different from the file name.
    # This is optional. Notice, attachment_name should have the same
    # file extension as the file.
    comment="Uploaded via elAPI",
    # We can pass an optional comment.
)
print(
    f"Successfully uploaded attachment '{ATTACHMENT_FILE}' to experiment ID {EXPERIMENT_ID}."
)
