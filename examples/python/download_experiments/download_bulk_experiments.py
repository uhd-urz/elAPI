# ╔─────────────────────────────────────╗
# │                                     │
# │    Download all experiments in      │
# │    organized directories/folders    │
# │                                     │
# ╚─────────────────────────────────────╝
# ---------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We have seen how we can download a single experiment before. Here we will adapt the same
# methods shown before to download all experiments. We will also store the experiments
# in an organized directory structure.
# E.g.: An <experiment> created in April 2024, will be stored in
# YYY_MM_DD_HHMMSS_Experiments/2024/April/<experiment ID>_<experiment name>.pdf
# We would also allow an option for other supported formats.
# ▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌
# ▐  Supported experiment download formats are:   ▌
# ▐  PDF, PDFA, ZIP, ZIPA, ELN, CSV, QRPNG        ▌
# ▐▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌
# JSON, YAML formats are also supported by elAPI, but here we care about more user-friendly formats.
# Note: elapi offers this feature via the CLI command as well.
# Run "elapi experiments get --help" to learn more.
# Here, we will implement the experiment download ourselves.
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
# 1. We first get the list of all experiment metadata.
# 2. We iterate over the list of experiment metadata.
# 3. Just like before: We make GET request to each experiment (with query) during iteration.
# 4. We store the downloaded experiment in an organized, date-based
# folder structure explained above.
# Note: we will use synchronous HTTP clients.
# For faster downloads, we can send requests asynchronously.
# For that, we can use RecursiveInformation class from elapi.plugins.commons.

# For date information to create folders
import calendar
from datetime import datetime
# To catch JSONDecodeError when parsing experiment metadata
from json import JSONDecodeError
from pathlib import Path
from typing import List, Union

# For catching network error
from httpx import HTTPError

# For handling HTTP connections
from elapi.api import FixedEndpoint
# For logging
from elapi.loggers import Logger
# For handling paths (An extension of Python pathlib's Path)
from elapi.path import ProperPath
# For terminating the program
from elapi.validators import Exit
# For making sure we have the appropriate permission
from elapi.validators import (
    Validate,
    ValidationError,
    HostIdentityValidator,
    PathValidator,
)

# First we create a FixedEndpoint instance with the endpoint of our interest "experiments" as its only argument.
experiment_endpoint = FixedEndpoint("experiments")

# We use Logger instance for logging errors and other messages
# Logs are printed to the terminal and to a local file.
# See the log file location from `elapi show-config`.
logger = Logger()

# We always need to make sure we are targeting the correct server with no foreseeable network issues.
# I.e., our API key/token is correct, the host address is valid, etc.
# If something is found to be wrong (or invalid) by the validator, elAPI will show the appropriate error message
# and quit.
validate = Validate(HostIdentityValidator())


# Note: The following method uses a synchronous solution.
# For faster downloads, we need to send requests asynchronously.
# For that, we can use RecursiveInformation class from elapi.plugins.commons.


def get_all_experiments_data() -> List[dict]:
    """
    eLabFTW doesn't send back all experiments at once but in batches.
    get_all_experiments_data function collects the experiment data from each batch
    until no batch is left. The collected list of all experiments is returned.
    """
    default_query: dict = {"scope": 2, "state": "1%2C2%2C3"}
    batch_response = experiment_endpoint.get(endpoint_id=None, query=default_query)
    try:
        all_experiments_data: List[dict] = (
            batch_response.json()
        )  # endpoint_id==None with no offset will get the first batch of experiments data
    except JSONDecodeError:
        # We catch any invalid JSON received.
        # Though this is unlikely to happen if there was no network error.
        logger.error(
            "Unexpected error occurred while decoding list of experiments."
            f"Received response: {batch_response.content}"
        )
        raise Exit(1)
    expected_limit = offset = len(all_experiments_data)
    continuous_batch = []
    while len(continuous_batch) != 0:
        continuous_batch_response = experiment_endpoint.get(
            endpoint_id=None, query={"offset": offset, **default_query}
        )
        try:
            continuous_batch = continuous_batch_response.json()
        except JSONDecodeError:
            logger.error(
                "Unexpected error occurred while decoding list of experiments."
                f"Received response: {continuous_batch_response.content}"
            )
        all_experiments_data.extend(continuous_batch)
        offset += expected_limit
    return all_experiments_data


def download_all_experiments(
    root_export_directory: Union[str, ProperPath, Path],
    format: str = "pdf",
):
    # +-----------------------------------+
    # |  Get the list of all experiments  |
    # +-----------------------------------+

    try:
        all_experiments_data = get_all_experiments_data()
    except HTTPError as e:
        logger.error(
            f"There was a network error in getting list of all experiments. "
            f"Exception details: {e}"
        )
        raise Exit(1)
        # We check if the given root_export_directory is indeed a directory and not a file!
    if not isinstance(root_export_directory, ProperPath):
        root_export_directory = ProperPath(root_export_directory)
    if root_export_directory.kind != "dir":
        logger.error("root_export_directory must be a directory!")
        raise Exit(1)
    # We validate the export directory location to make sure we have permission to write the directory
    try:
        root_export_directory = Validate(PathValidator(root_export_directory)).get()
    except ValidationError as e:
        logger.error(e)
    # We will store all experiments in a folder with a unique name
    # every time download_all_experiments is called.
    main_directory_name: str = (
        f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_Experiments"
    )
    # +----------------------------------------+
    # |  Iterate over the list of experiments  |
    # +----------------------------------------+
    for experiment in all_experiments_data:
        experiment_id = experiment["id"]  # Get experiment ID
        experiment_title = experiment["title"]  # Get experiment title
        experiment_creation_date = datetime.fromisoformat(
            experiment["created_at"]
        )  # Get experiment creation date
        # Get experiment creation year and month
        experiment_creation_year, experiment_creation_month = (
            str(experiment_creation_date.year),
            calendar.month_name[experiment_creation_date.month],
        )
        # We define the final directory where experiment will be stored.
        # elAPI's ProperPath is an extended class of Python pathlib's Path.
        export_directory = ProperPath(
            (
                root_export_directory
                / main_directory_name
                / experiment_creation_year
                / experiment_creation_month
            ),
            kind="dir",
        )
        try:
            # We create the directory first.
            export_directory.create(verbose=False)
        except export_directory.PathException as e:
            logger.error(e)
            raise Exit(1)
        try:
            # +-----------------------------------------------------+
            # |  Download each experiment in PDF                    |
            # |  (default format of our function) during iteration  |
            # +-----------------------------------------------------+
            experiment_in_format = experiment_endpoint.get(
                experiment_id, query={"format": format}
            )
        except HTTPError as e:
            logger.error(
                f"There was a network error in getting experiment '{experiment_title}' "
                f"with ID '{experiment_id}'. Exception details: {e}"
            )
            raise Exit(1)
        else:
            if not experiment_in_format.is_success:
                logger.error(
                    f"There was an error in getting experiment '{experiment_title}' "
                    f"with ID '{experiment_id}'. Received response: {experiment_in_format.content}"
                )
                raise Exit(1)
            # export_location is the final path where the experiment will be stored
            export_location = (
                export_directory / f"{experiment_id}_{experiment_title}.{format}"
            )
            # +-----------------------------------------+
            # |  Store the downloaded experiment in a   |
            # |  date-based organized file structure    |
            # +-----------------------------------------+
            with export_location.open(mode="wb") as f:
                f.write(experiment_in_format.content)
            logger.info(
                f"Experiment '{experiment_title}' successfully exported to "
                f"{export_location} in '{format}' format."
            )


if __name__ == "__main__":
    from elapi.styles import stdout_console  # For printing pretty text formatting

    # +------------------+
    # |  Run validation  |
    # +------------------+
    # We still haven't run the validation yet.
    # First, run validation by just calling the "validate" instance.
    with stdout_console.status("[bold]Validating...[/bold]\n"):
        validate()
    stdout_console.print("[bold green]Validation complete.[bold green]")
    stdout_console.print("\n")
    stdout_console.print("[bold]Download started...[/bold]\n")
    # +------------------------------------------+
    # |  Call download_all_experiments function  |
    # +------------------------------------------+
    download_all_experiments(
        root_export_directory="~/Downloads/eLab_experiments", format="zip"
    )  # We change the format to 'zip'
    stdout_console.print("\n")
    stdout_console.print("[bold green]Download complete.[bold green]\n")
    # We have to close the session(s) manually.
    experiment_endpoint.close()
