# elAPI

elAPI is a powerful, extensible API client for eLabFTW built for
the [University Computing Centre](https://www.urz.uni-heidelberg.de/en) (
URZ, [FIRE](https://www.urz.uni-heidelberg.de/en/node/64/organisation/future-it-research-education) division) at
Universität Heidelberg. It supports serving almost all kinds of requests documented on
[eLabFTW API documentation](https://doc.elabftw.net/api/v2/) with ease. elAPI treats eLabFTW API endpoints as its
arguments.

**Example:**

From [the documentation](https://doc.elabftw.net/api/v2/#/Users/read-user):
> GET /users/{id}

With elAPI you can do the following:

```sh
$ elapi get users --id <id>
```

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
# You can generate an API token from eLabFTW user panel -> API keys tab.
export_dir: ~/Downloads/elAPI
unsafe_api_token_warning: yes
enable_http2: no
```

`export_dir` is where elAPI will export response content to if no path is provided to `--export/-E`.
When `unsafe_api_token_warning` is `True`, elAPI will show a warning if you're storing `elapi.yml` in the current
working directory, as it typically happens that developers accidentally commit and push configuration files with
secrets. `enable_http2` enables HTTP/2 protocol support which by default is turned off. Be aware
of [known issues](https://github.com/encode/httpx/discussions/2112) with
HTTP/2 if you are making async requests with heavy load.

You can get an overview of detected configuration with `elapi show-config`. `show-config` makes it easier to verify
which configuration values are actually used by elAPI, if you are working with multiple configuration files.

```shell
$ elapi show-config


                                                       elapi configuration information

The following debug information includes configuration values and their sources as detected by elapi.

▌ Name [Key]: Value ← Source

 • Log file path: /Users/<username>/.local/share/elapi/elapi.log
 • Host address [host]: https://demo.elabftw.net/api/v2 ← USER LEVEL
 • API Token [api_token]: 00-55******55555 ← USER LEVEL
 • Export directory [export_dir]: /Users/<username>/Downloads/elapi ← USER LEVEL
 • App data directory: /Users/<username>/.local/share/elapi
 • Caching directory: /private/var/tmp/elapi
 • Unsafe API token use warning [unsafe_api_token_warning]: Yes ← USER LEVEL
 • Enable HTTP/2 [enable_http2]: Yes ← USER LEVEL

Detected configuration sources that are in use:

 • USER LEVEL: /Users/<username>/.config/elapi.yml

```

If both `host` and `api_token` are detected, you are good to go!

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

### Bill teams

You can get a list of all teams and its users for billing purposes and export it to home directory.

```shell
$ elapi bill-teams teams-info --export ~
```

Most sub-commands available under `elapi bill-teams` plugin are for Universität Heidelberg specific use-cases.

## Open-source

elAPI is open-source and published under AGPLv3 license. The repository is however hosted internally within
Universität Heidelberg's network. The codebase can still be accessed from [PyPI](https://pypi.org/project/elapi/#files).
If you express interest in having the repository made completely public, or if you have any question, feel free
to [contact us](mailto:elabftw@uni-heidelberg.de).