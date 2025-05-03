# ╔─────────────────────────────────────────────╗
# │                                             │
# │    Download a single experiment             │
# │    in PDF (or in other supported format)    │
# │                                             │
# ╚─────────────────────────────────────────────╝
# -----------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We would like to download an existing experiment in PDF. We would also allow an option for
# other supported formats.
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
# Note: The elAPI we installed through pipx remains isolated, only meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. We define the function "download_single_experiment" which will make the GET request.
# 2. We pass the experiment ID and "query" field with our desired "format" to the GET request API.
# 3. We define an export directory with Export class.
# 4. We store the retrieved data from step 2 by calling the export instance of Export class.

# For handling HTTP connections
from elapi.api import FixedEndpoint

# For storing downloading experiment
from elapi.plugins.commons import Export

# First we create a FixedEndpoint instance with the endpoint of our interest "users" as its only argument.
experiment_endpoint = FixedEndpoint("experiments")


def download_single_experiment(
    experiment_id: str, format: str = "pdf", export_directory: str = "~/Downloads"
):
    experiment = experiment_endpoint.get(experiment_id, query={"format": format})
    # E.g.: GET request to experiment <ID> with query {"format": PDF}.
    experiment_title = experiment_endpoint.get(experiment_id).json()["title"]
    # We save the experiment title to variable experiment_title because we want to use
    # the title as our download file name.
    export = Export(
        export_directory,
        file_name_stub=experiment_title,
        file_extension=format,
        format_name=format,
    )
    # We use Export class because it takes care of what kind path we want to export to.
    # We can pass a directory or a file location as the first positional argument to Export.
    # If a path is a directory, Export will create the actual file for us, based on given
    # file_name_stub and file_extension. format_name is the actual format of the file
    # (in case, file format and file extension differ).

    if experiment.is_success:
        # We call the Export instance "export" when the request is a success.
        # verbose==True will print/log a success message.
        export(experiment.content, verbose=True)
    else:
        # We print a success message for successful account creation, or
        # an error message in the case of an error. This is a simple STDOUT print.
        # In the advanced implementation, we will print to STDERR.
        print(f"There was an error downloading experiment with ID '{experiment_id}'.")


if __name__ == "__main__":
    download_single_experiment("129", export_directory="~/Downloads", format="pdf")
    # Try it yourself: Change format to one of the supported formats!
    # Finally, we close the session.
    experiment_endpoint.close()
