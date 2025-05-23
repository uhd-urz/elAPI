# ╔─────────────────────────────────────╗
# │                                     │
# │    Create an elAPI plugin           │
# │                                     │
# ╚─────────────────────────────────────╝
# ---------------------------------------
# ┌─────────────┐
# │  Objective  │
# └─────────────┘
# We will write a really simple third-party elAPI plugin script that sends a GET request to eLabFTW endpoint.
# ┌────────────────┐
# │  Requirements  │
# └────────────────┘
# - The code seen in this file must be placed inside ~/.local/share/elapi/plugins/awesome/cli.py
# Since this is a third-part plugin, we don't necessarily need elapi inside a virtual environment.
# elAPI must be installed as a CLI tool via `uv tool` or `pipx`
# ┌─────────────────┐
# │  Code overview  │
# └─────────────────┘
# We explain in comments around each significant line of code what the code does.
# Here we will give a short overview:
# 1. We define the plugin interface that elAPI can understand
# 2. We define a simple function that makes a GET request to eLabFTW


from elapi.api import GETRequest
from elapi.plugins.commons import Typer

# Plugin interface. The plugin name here must match the plugin directory this file is in
app = Typer(name="awesome", help="An awesome elAPI plugin.")


# More documentation about the app instance can be found on https://typer.tiangolo.com/tutorial/commands/
@app.command(name="get-request", short_help=f"Make a GET request")
def get_request(endpoint_name):
    # get_request accepts an endpoint name as a positional argument that can be passed via the CLI
    r = GETRequest()
    # Here, we just simple show what the endpoint returns
    print(r(endpoint_name).json())


# Now you will be able to run `elapi awesome`.
# Try running `elapi awesome get-request info`
