<p align="center">
<img src="https://heibox.uni-heidelberg.de/f/43bdc63b9458478e949f/?dl=1" alt="elAPI logo" width=120 />
</p>

<p align="center">
   <a href="https://pypi.org/project/elapi">
<img alt="Package version" src="https://badge.fury.io/py/elapi.svg/?branch=main" />
   </a>
<a href="#compatibility">
   <img alt="Static Badge" src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-%230d7dbe">
   <img alt="Static Badge" src="https://img.shields.io/badge/eLabFTW%20support-4.5%2B%20%7C%205.0%20%7C%205.1-%2323b3be">
</a>
</p>

elAPI is a powerful, extensible API client for [eLabFTW](https://www.elabftw.net/) developed at
the [University Computing Centre](https://www.urz.uni-heidelberg.de/en) (
URZ, [FIRE](https://www.urz.uni-heidelberg.de/en/node/64/organisation/future-it-research-education) division)
of [University of Heidelberg](https://www.uni-heidelberg.de/en). elAPI has complete support
for [eLabFTW REST APIv2](https://doc.elabftw.net/api/v2/). elAPI executable comes with a simple CLI interface for
performing fast and quick API tasks. elAPI Python package brings a suite of convenience APIs to help streamline advanced
API automation tasks. Check out our [examples](#examples-and-usage).

<img src="https://heibox.uni-heidelberg.de/f/7714c7eeb0f54a3ba318/?dl=1" alt="elAPI features in a nutshell" />

**Example:**

From [the API documentation](https://doc.elabftw.net/api/v2/#/Users/read-user):
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

We recommend either [`uv`](https://docs.astral.sh/uv/concepts/tools/) or [`pipx`](https://pipx.pypa.io/stable/) for
installing elAPI for use of its CLI functionalities. Both uv and Pipx
install packages in isolated virtual environments, so elAPI installed as a CLI tool should not conflict with elAPI
installed inside other virtual environments.

```shell
$ uv tool install elapi
# elAPI can be updated to the latest version with 
# uv tool upgrade elapi
```

After installation with `uv` is complete, you would also be able to run elAPI just by entering the `elapi` command on
the terminal. You can move on to ["Getting started"](#getting-started).

### Advanced installation

elAPI can be used both as a CLI tool and as a Python library. If you are interested in simply using elAPI's
off-the-shelf features from the command-line, install elAPI as a CLI tool (see ["Installation"](#installation)). If you
intend to write an automation script for eLabFTW, you should install elAPI as a library inside a virtual environment. Of
course, if you need both, you can have elAPI installed in both ways.

> [!NOTE]
> Support for installing Python packages with `pip install --user` has been deprecated with the adoption
> of [PEP 688](https://peps.python.org/pep-0668/) on many systems
> like [Debian 12](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1030335#5).

### Installing elAPI as a library

It is recommended to install elAPI inside a Python virtual environment with your preferred package manager (`pip`,
`poetry`, `pipenv`, `rye`, `uv`, etc.). With `uv`, for example, run `uv add elapi`. From inside a virtual environment,
elAPI CLI can be invoked with `python -m elapi.cli`. At the moment, though, the documentation about using elAPI as a
library is severely lacking.

## Getting started

Once you have elAPI [installed](#installation), to **quickly** get started, run `elapi init`. You will be prompted with
questions about your eLabFTW server with examples to help you fill in the answers. Here's a demo:

```shell
$ elapi init
```

<video src='https://github.com/user-attachments/assets/8d5f69ed-b644-4d75-b816-d06d4e937105'> </video>
<p align="center">elapi init demo</p>

That's all! Run [`elapi whoami`](#elapi-whoami) to see a short summary of your eLab user. Run [
`elapi show-config`](#show-config) to view
your configuration details.

## Compatibility

elAPI is compatible with the following Python versions: `3.11`, `3.12`. elAPI supports
the [eLabFTW REST API v2](https://doc.elabftw.net/api/v2/), and can be used with the following eLabFTW
versions: `4.5`, `4.6`, `4.7`, `4.8`, `4.9`, `4.10`, `5.0`, `5.1`, `5.2`, and above.

## Configuration

elAPI needs to be configured first before you can do anything useful with it. Mainly, elAPI needs to know your eLabFTW
server's API URL and your API key (or token) for access. See a quick configuration method
in "[Getting started](#getting-started)" before you dive into the advanced settings.

### Advanced configuration

elAPI supports a YAML configuration file in the following locations.

- Current directory: `./elapi.yml`
- User directory: `$HOME/.config/elapi.yml`
- Root directory: `/etc/elapi.yml`

elAPI supports configuration overloading. I.e., a keyword set in root configuration file `/etc/elapi.yml` can be
overridden by setting a different value in user configuration file `$HOME/.config/elapi.yml`. In terms of precedence,
a configuration file present in the currently active directory has the highest priority, and a configuration file in the
root directory has the lowest.

The following parameters are currently configurable, with `host` and `api_token` being the required fields.

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
async_rate_limit: 20
async_capacity: 500
development_mode: false
```

- `export_dir` is where elAPI will export response content to if no path is explicitly provided to `--export/-E`.
- When `unsafe_api_token_warning` is `True`, elAPI will show a warning if you're storing `elapi.yml` in the current
  working directory, as it typically happens that developers accidentally commit and push configuration files with
  secrets.
- `enable_http2` enables HTTP/2 protocol support which by default is turned off. Be aware
  of [known issues](https://github.com/encode/httpx/discussions/2112) with HTTP/2 if you are making async requests with
  a heavy load.
- `verify_ssl` can be turned off with value `False` if you are
  trying out a development server that doesn't provide a valid SSL certificate.
- `timeout` can be modified to your needs. E.g., a poor internet connection might benefit from a higher timeout number.
  The default timeout is `90` seconds.
- `async_rate_limit` controls the maximum number of requests per second (i.e., throughput) you want to make to the
  server. The default `async_rate_limit` is `null` which means no limit. An eLab server might be configured to limit
  a high number of requests to prevent spam, `async_rate_limit` can then be set to the maximum number of requests
  allowed by the server.
- `async_capacity` controls the maximum number of in-flight async requests. The default `async_capacity` is `null` which
  means no limit on capacity. Both `async_rate_limit` and `async_capacity` can be used to better limit the traffic load
  put on the server. See this [SA answer](https://stackoverflow.com/a/52100884/7696241) about how they differ from each
  other.
- `development_mode` can be set to `True` to show debug logs, Python traceback on the CLI instead of a clean exit, etc.
  This mode should not be turned on for production-ready scripts.

### `show-config`

You can get an overview of detected configuration with `elapi show-config`. `show-config` makes it easier to verify
which configuration values are actually used by elAPI – especially if you are working with multiple configuration files.

```shell
$ elapi show-config  # host username: "culdesac" 
```

![elAPI show-config output](https://heibox.uni-heidelberg.de/f/00a8dabbf2124087aae4/?dl=1)

If both `host` and `api_token` are detected, you are good to go!

### Overriding configuration

elAPI now supports `--override/--OC` as a global option that can be used to override the configuration parameters
as detected by `elapi show-config`. All plugins will also automatically listen to the overridden configuration. This can
be useful to set certain configurations temporarily. E.g., `elapi --OC '{"timeout": 300"}' get info` will override
the `timeout` from the configuration files.

## elAPI `whoami`

Oftentimes, you work with multiple API tokens/keys for multiple teams on multiple eLab servers. elAPI enables robust
workflow management with built-in [advanced configuration](#advanced-configuration) orchestration. During development
though,
juggling between multiple API keys can still lead to confusion as to which API key is being actually used. elAPI version
`2.4.1` adds the `whomai` command that shows the essential information about the requesting eLab user.

```shell
$ elapi whoami
```

![elapi whoami output](https://heibox.uni-heidelberg.de/f/e3096d5659db45e58a94/?dl=1)

So, if your API task requires write permission, but only `Read-only` is shown next to the API key, you know you're using
the wrong API key. But having to run `elapi whoami` every single time for this would be cumbersome. So, we added the
`whoami` information to the debug messages. To enable debug messages, set `development_mode` to `True` in
the [configuration file](#configuration). Once set, before any elAPI command and plugin is run, elAPI will show the
`whoami` information in the debug messages.

```shell
DEBUG    Based on the detected configuration, the requests will be made to the server                                         get_whoami.py:114
         https://elabftw-dev-002.uni-heidelberg.de (eLabFTW version: 5.2.8), with API token '84-fc******2a384' (Read/Write),
         by user 'John Doe' (ID: 2607), from team 'North Kathy' (ID: 19), in user group 'User', not as a sysadmin. Scopes:
         experiments = 'Team', items = 'Team', experiments_templates = 'Team', teamgroups = 'Everything'
```

## Examples and usage

Check out the [examples directory](https://github.com/uhd-urz/elAPI/tree/main/examples) for some comprehensive code
examples with elAPI. elAPI CLI usage details can be displayed with:

```shell
$ elapi --help

```

### `GET` requests

Request an overview of a running eLabFTW server:

```shell
$ elapi get info -F yml
# Here -F (or --format) defines the output format
```

You can request a list o all active experiments and export it to a `JSON` file.

```shell
$ elapi get experiments --export ~/Downoads/experiments.json
```

Enable built-in syntax highlighting with `--highlight` or `-H`. Here, the following command will fetch team information
of the team with team ID 1.

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

Delete all the tags associated with an experiment:

```shell
$ elapi delete experiments -i <experiment ID> --sub tags
```

You can reset the configuration to default values.

```shell
$ elapi delete config
```

### `experiments` built-in plugin

`experiments` plugin enables experiments-specific actions. You can download an experiment in PDF by its "Unique eLabID"
to `~/Downloads` directory.

```shell
$ elapi experiments get -i <experiment unique elabid> -F pdf --export ~/Downloads/
```

Append text in Markdown to an existing experiment by its ID:

```shell
$ elapi experiments append --id <experiment ID> -M -t "**New content.**"
```

You can also upload an attachment to an experiment.

```shell
$ elapi experiments upload-attachment --id <experiment ID> --path <path to attachment file> --comment <comment for your attachment>
```

### `mail` built-in plugin

Sometimes when a script has finished, you and your team would want to receive an email about its success/failure. elAPI
offers a no-code solution for this: the `mail` plugin. The `mail` plugin is not enabled by default. To enable it,
install elAPI with the optional dependency `mail`: `pip install elapi[mail]` or `uv add elapi[mail]`. [__See the wiki
__](https://github.com/uhd-urz/elAPI/wiki/mail-plugin) to read more about how to configure the `mail` plugin with your
mail server configuration and trigger conditions. In a
nutshell, the `mail` plugin will scan the logs when a script/plugin is done to look for pre-configured trigger
conditions, and if found, it will send an email. The trigger conditions can be atomic and scope-based, i.e., an email
can be sent only when a specific plugin task/command is finished, and/or when a matching log state and/or a matching log
pattern is found.

<img alt="elAPI email trigger screenshot" src="https://github.com/user-attachments/assets/2dc0df3e-0d91-41f3-af28-4040da641a70" />

## Creating a plugin

elAPI has seamless support with tight integration for third-party plugins. A simple third-party plugin can be created in
a few easy steps:

1. Create a new subfolder under `~/.local/share/elapi/plugins` with the name for your new plugin (e.g., a folder named
   "test")
2. Create a `cli.py` in the subfolder with the following snippet:

```python
from elapi.plugins.commons import Typer

app = Typer(name="test", help="Test plugin.")

```

3. Run `elapi` again to see your plugin name under `Third-party plugins` list

Plugins are integrated in a way such that a plugin will **not** fail elAPI. So, even if one erroneous plugin is loaded,
all other plugins and elAPI itself will remain unaffected. elAPI will show the error message on the "Message" panel.

If you try to import a package that is not a dependency of elAPI inside `cli.py`, your plugin will fail. In that case,
you want to create a plugin metadata file `elapi_plugin_metadata.yml` (notice only `.yml` extension is allowed), and
define the virtual environment that your plugin specifically requires.

```python
import requests  # A third-party dependency

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

And, the path to the virtual environment will be defined in the metadata file:

```yaml
# elapi_plugin_metadata.yml
plugin_name: awesome
cli_script: ~/awesome/cli.py  # Path to the cli.py script
venv_dir: ~/awesome/.venv  # Path to the virtual environment
project_dir: ~/awesome  # Path to the project root directory where the plugin is located
```

This metadata file of plugin `awesome` must be placed inside `~/.local/share/elapi/plugins/awesome`. Notice, the plugin
name must also match the parent directory name of `elapi_plugin_metadata.yml`. This way we ensure a plugin name remains
unique.
