# ╔─────────────────────────────────────────────╗
# │                                             │
# │    Download an attachment by its ID or      │
# │    hash from an experiment                  │
# │                                             │
# ╚─────────────────────────────────────────────╝
# -----------------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# Given an experiment ID and an attachment ID, we would like to download that attachment.
# elAPI CLI also offers this as a feature. See: "elapi experiments download-attachment --help"
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The minimum Python version required is 3.9. It's recommended that we create a
# Python virtual environment, and we run/edit the script from inside the environment.
# - We need to install elAPI from inside the activated virtual environment.
# Simple `uv add elapi` or `pip install elapi` will work.
# Note: The elAPI we installed through uv tool or pipx remains isolated, meant to work as
# a user-friendly CLI tool. Here, we want to use elAPI as a library.
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. We mainly use the download_attachment function provided by elAPI "experiments" plugin
# that returns the attachment (in binary) itself, and its metadata like
# attachment name, attachment extension, etc.
# 2. We store the attachment with elapi Export.

from pathlib import Path
from typing import Union

# For exporting the final attachment to a file
from elapi.plugins.commons import Export
# download_attachment takes care of the request for downloading the attachment
from elapi.plugins.experiments import download_attachment
# stdout_console offers print methods with styles
from elapi.styles import stdout_console
# For making sure we have the appropriate permission
from elapi.validators import Validate, HostIdentityValidator


# For handling paths (An extension of Python pathlib's Path)


def download_single_attachment(
    experiment_id: Union[str, int],
    attachment_id: Union[str, int],
    export_dest: Union[str, Path],
) -> None:
    # We always need to make sure we are targeting the correct server with no foreseeable network issues.
    # I.e., our API key/token is correct, the host address is valid, etc.
    # If something is found to be wrong (or invalid) by the validator, elAPI will show the appropriate error message
    # and quit.
    validate_config = Validate(HostIdentityValidator())
    validate_config()

    # stdout_console is a Rich "Console" instance that gives as an animated spinner
    with stdout_console.status("Downloading attachment...", refresh_per_second=15):
        # download_attachment accepts the experiment ID and the attachment ID as its
        # real ID or SHA hash seen on an experiment page. It returns the
        # attachment metadata as well. attachment_creation_date can be used
        # to create a structure of date-based folders and store attachments in
        # the respective folders.
        (
            attachment,
            attachment_real_id,
            attachment_name,
            attachment_extension,
            attachment_hash,
            attachment_creation_date,
        ) = download_attachment(experiment_id, attachment_id)
        # If you are interested, under the hood,
        # "download_attachment" uses the following snippet of code
        # for getting the attachment
        # session = FixedEndpoint("experiments")
        # attachment = session.get(
        #     experiment_id,
        #     sub_endpoint_name="uploads",
        #     sub_endpoint_id=attachment_id,
        #     query={"format": "binary"},
        # ).content

    # We use the attachment ID/hash as the downloaded attachment name
    _is_real_id = attachment_id == attachment_real_id
    file_name_stub = (
        f"attachment_{attachment_real_id if _is_real_id else attachment_hash[:6]}_"
        f"{attachment_name}"
    )
    # Export automatically adds a timestamp to the file name
    # We could also just write the attachment to a file with export_dest.open() or just open()
    export_attachment = Export(
        export_dest,
        file_name_stub=file_name_stub,
        file_extension=attachment_extension,
        format_name=attachment_extension,
    )
    export_attachment(data=attachment, verbose=True)


if __name__ == "__main__":
    download_single_attachment(
        experiment_id=147,
        attachment_id=426,  # Or attachment hash
        export_dest="~/Downloads",  # The download location
    )
