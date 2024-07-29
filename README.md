# elAPI

[![Package version](https://badge.fury.io/py/elapi.svg/?branch=main)](https://pypi.org/project/elapi)

elAPI is a powerful, extensible API client for eLabFTW developed at
the [University Computing Centre](https://www.urz.uni-heidelberg.de/en)
(URZ, [FIRE](https://www.urz.uni-heidelberg.de/en/node/64/organisation/future-it-research-education) division) of
[University of Heidelberg](https://www.uni-heidelberg.de/en). It supports serving all kinds of requests documented on
[eLabFTW API documentation](https://doc.elabftw.net/api/v2/) with ease. elAPI provides a simple interface via its CLI
executable, and numerous advanced APIs when it is used directly as a Python package.

<img src="https://heibox.uni-heidelberg.de/f/7714c7eeb0f54a3ba318/?dl=1" alt="elAPI features in a nutshell" />

**Example:**

From [the documentation](https://doc.elabftw.net/api/v2/#/Users/read-user):
> GET /users/{id}

With elAPI you can do the following:

```sh
$ elapi get experiments --format csv --export ~/Downloads/
```

Once the command is run, in the background, elAPI will read host (eLab server) address, API key and various other
settings (see [configuration](#configuration)) from the configuration file `elapi.yml`, perform validation (e.g.,
whether the server address is valid), fetch all _experiments_ list, convert them to `CSV`, and export them to your
local `~/Downloads/` folder.

## Installation

elAPI can be used both as a CLI tool and as a Python library. If you are interested in simply using elAPI's
off-the-shelf features from the command-line, install elAPI as a CLI tool. If you intend to write automation script for
eLabFTW, you should install elAPI as a library inside a virtual environment. Of course, if you're interested in
both, you can have elAPI installed in both ways.

### Install elAPI as a CLI tool

Support for installing Python packages with `pip install --user` has been deprecated with the adoption
of [PEP 688](https://peps.python.org/pep-0668/) on many systems
like [Debian 12](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1030335#5).
We recommend [`pipx`](https://pipx.pypa.io/stable/) for installing elAPI for use of its CLI functionalities. Pipx
installs packages in isolated virtual environments, so Pipx-installed elAPI should not conflict with elAPI installed
inside other virtual environments.

```shell
$ pipx install elapi
```

After installation with Pipx is complete, you would also be able to run elAPI just by entering the `elapi` command on
the
terminal.

### Install elAPI as a library

It is recommended to install elAPI inside a Python virtual environment for use of its rich APIs for
working with eLabFTW. From inside a virtual environment, elAPI CLI can be invoked with `python -m elapi.cli`.
At the moment, though, the documentation about using elAPI as a library is severely lacking.

## Configuration

elAPI needs to be configured first before you can do anything useful with it. Mainly, elAPI needs to know your eLabFTW
server's API URL and your API key (or token) for access.

### Quick configuration

You can run `elapi init` to simplify the configuration process. You will be prompted with questions
about your eLabFTW server with examples to help you fill in the answers.

### Advanced configuration

elAPI supports a YAML configuration file in
the following locations.

- Current directory: `./elapi.yml`
- User directory: `$HOME/.config/elapi.yml`
- Root directory: `/etc/elapi.yml`

elAPI supports configuration overloading. I.e., a keyword set in root configuration file `/etc/elapi.yml` can be
overridden by setting a different value in user configuration file `$HOME/.config/elapi.yml`. In terms of precedence,
configuration file present in the currently active directory has the highest priority, and configuration in root
directory has the lowest.

The following parameters are currently configurable, with `host` and `api_token` being the required fields. For testing
purposes, it would be safe to store everything in `$HOME/.config/elapi.yml`.

```yaml
# elAPI configuration
# Saved in `$HOME/.config/elapi.yml`

host: <host API url>
# Example: https://demo.elabftw.net/api/v2/
# Note the host URL ends with the API endpoint
api_token: <token with at least read-access>
# "A.k.a API key". You can generate an API token from eLabFTW user panel -> API keys tab.
export_dir: ~/Downloads/elAPI
unsafe_api_token_warning: true
enable_http2: false
verify_ssl: true
timeout: 90
```

`export_dir` is where elAPI will export response content to if no path is provided to `--export/-E`.
When `unsafe_api_token_warning` is `True`, elAPI will show a warning if you're storing `elapi.yml` in the current
working directory, as it typically happens that developers accidentally commit and push configuration files with
secrets. `enable_http2` enables HTTP/2 protocol support which by default is turned off. Be aware
of [known issues](https://github.com/encode/httpx/discussions/2112) with
HTTP/2 if you are making async requests with a heavy load. `verify_ssl` can be turned off with value `False` if you are
trying
out a development server that doesn't provide a valid SSL certificate. `timeout` can be modified to your needs. E.g., a
poor internet connection might benefit from a higher timeout number. The default timeout is `90` seconds.

### `show-config`

You can get an overview of detected configuration with `elapi show-config`. `show-config` makes it easier to verify
which configuration values are actually used by elAPI, if you are working with multiple configuration files.

```shell
$ elapi show-config

elapi configuration information

The following debug information includes configuration values and their sources as detected by elapi.

▌ Name [Key]: Value ← Source

• Log file path: /Users/ <username >/.local/share/elapi/elapi.log
• Host address [host]: https://demo.elabftw.net/api/v2 ← USER LEVEL
• API Token [api_token]: 00-55******55555 ← USER LEVEL
• Export directory [export_dir]: /Users/ ← USER LEVEL <username >/Downloads/elapi
• App data directory: /Users/ <username >/.local/share/elapi
• Third-party plugins directory: /Users/ <username >/.local/share/elapi/plugins
• Caching directory: /private/var/tmp/elapi
• Unsafe API token use warning [unsafe_api_token_warning]: True ← USER LEVEL
• Enable HTTP/2 [enable_http2]: False ← USER LEVEL
• Verify SSL certificate [verify_ssl]: True ← USER LEVEL
• Timeout duration [timeout]: 90.0 seconds ← USER LEVEL
• Development mode [development_mode]: False ← USER LEVEL

Detected configuration sources that are in use:

• USER LEVEL: /Users/ <username >/.config/elapi.yml

```

If both `host` and `api_token` are detected, you are good to go!

### Override configuration

elAPI now supports `--override/--OC` as a global option that can be used to override the configuration parameters
as detected by `elapi show-cofig`. All plugins will also automatically listen to the overridden configuration. This can
be useful to set certain configurations temporarily. E.g., `elapi --OC '{"timeout": 300"}' get info` will override
the `timeout` from the configuration files.

## Usage

elAPI can be invoked from the command-line.

```shell
$ elapi --help 
```

### `GET` requests

Request an overview of running eLabFTW server:

```shell
$ elapi get info -F yml
# Here -F (or --format) defines the output format
```

You can request a list o all active experiments and export it to a `JSON` file.

```shell
$ elapi get experiments --export ~/Downoads/experiments.json
```

Enable built-in syntax highlighting with `--highlight` or `-H`. Here, the following command will fetch team information
of team with team ID 1.

```shell
$ elapi get -H teams --id 1
```

### `POST` requests

Create a new user by the name 'John Doe':

```shell
$ elapi post users --id <user id> -d '{"firstname": "John", "lastname": "Doe", "email": "test_test@itnerd.de"}'
```

### `PATCH` requests

Update an existing user's email address:

```shell
$ elapi patch users --id <user id> -d '{"email": "new_email@itnerd.de"}'
```

`patch` command allows us to make changes to eLabFTW server settings. E.g., you can update the time (in minutes)
after which the authentication cookie will expire.

```shell
$ elapi patch config -d '{"cookie_validity_time": 43200}'
```

You can publish an announcement to all the members.

```shell
$ elapi patch config -d '{"announcement": "Notice: Server will be down tomorrow at midnight due to scheduled maintenance."}'
```

### `DELETE` requests

Delete all the tags associated to an experiment:

```shell
$ elapi delete experiments -i <experiment ID> --sub tags
```

You can reset the configuration to default values.

```shell
$ elapi delete config
```

### `experiments` plugin

`experiments` plugin enables experiments-specific actions. You can download an experiment in PDF by its "Unique eLabID"
to `~/Downloads` directory.

```shell
$ elapi experiments get -i <experiment unique elabid> -F pdf --export ~/Downloads/
```

Append text in markdown to an existing experiment by its ID:

```shell
$ elapi experiments append --id <experiment ID> -M -t "**New content.**"
```

You can also upload an attachment to an experiment.

```shell
$ elapi experiments upload-attachment --id <experiment ID> --path <path to attachment file> --comment <comment for your attachment>
```

### Plugins

elAPI has seamless support with tight-integration for third-party plugins. A simple third-party plugin can be created in
a few easy steps:

1. Create a new subfolder under `~/.local/share/elapi/plugins` with the name for your new plugin (e.g, a folder named
   "test")
2. Create a `cli.py` in the subfolder with the following snippet:

```python
from elapi.plugins.commons import Typer

app = Typer(name="test", help="Test plugin.")

```

3. Run `elapi` again to see your plugin name under `Third-party plugins` list

Plugins are integrated in a way such that a plugin will **not** fail elAPI. So, even if one erroneous plugin is loaded,
all
other plugins and elAPI itself will remain unaffected. elAPI will show the error message on the "Message" panel.

If you try to import a package that is not a dependency of elAPI inside `cli.py`, your plugin will fail. In that case,
you want to create a plugin metadata file `elapi_plugin_metadata.yml` (notice only `.yml` extension is allowed), and
define the virtual environment that your plugin specifically requires.

```python
import requests

from elapi.api import GETRequest
from elapi.plugins.commons import Typer

# Plugin metadata
app = Typer(name="awesome", help="An awesome elAPI plugin.")


@app.command(name="get-request", short_help=f"Make a GET request")
def get_request(endpoint_name):
    r = GETRequest()
    print(r(endpoint_name).json())


@app.command(name="get-wiki-status", short_help=f"Show status of Wikipedia")
def wiki_status():
    r = requests.get("https://wikipedia.org")
    print(r)
```

And the path to virtual environment will be defined in the metadata file:

```yaml
plugin_name: test
cli_script: ./cli.py  # Path to the cli.py script
venv_dir: ./.venv  # Path to the virtual environment
```
