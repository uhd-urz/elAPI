# elAPI

elAPI is a powerful, extensible API interface to eLabFTW. It supports serving almost all kinds of requests documented in
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

elAPI can be installed from PyPI. Make sure `pip` is not invoked from an active virtual environment.

```sh
$ python3 -m pip install --user elapi
```

## Configuration

elAPI needs to be configured first before we can do anything useful with it. elAPI supports a YAML configuration file in
the following locations.

- Current directory: `./elapi.yaml`
- User directory: `$HOME/.config/elapi.yaml`
- Root directory: `/etc/elapi.yaml`

elAPI supports configuration overloading. I.e., a keyword set in root configuration file `/etc/elapi.yaml` can be
overriden by setting a different value in user configuration file `$HOME/.config/elapi.yaml`. In terms of precedence,
configuration file present in the currently active directory has the highest priority, and configuration in root
directory has the lowest.

The following parameters are currently configurable, with `host` and `api_token` being the required fields. For testing
purposes it would be safe to store everything in the user configuration file.

```yaml
# elAPI configuration
# Saved in `$HOME/.config/elapi.yaml`

host: <host API url>
# Example: https://demo.elabftw.net/api/v2/
# Note the host URL ends with the API endpoint
api_token: <token with at least read-access>
# You can generate an API token from eLabFTW user panel -> API keys tab.
export_dir: ~/Downloads/elAPI
unsafe_api_token_warning: yes
```

We can get an overview of detected configurations.

```shell
$ elapi show-config
```

If both `host` and `api_token` are detected, we are good to go!

## Usage

elAPI can be invoked from the command-line.

```shell
$ elapi --help 
```

### `GET` requests

We can request an overview of running eLabFTW server.

```shell
$ elapi get info -F yaml
# Here -F (or --format) defines the output format
```

We can request a list o all active experiments and export it to a `JSON` file.

```shell
$ elapi get experiments --export ~/Downoads/experiments.json
```

### `POST` requests

We can create a new user by the name 'John Doe'.

```shell
$ elapi post users -d '{"firstname": "John", "lastname": "Doe", "email": "test_test@itnerd.de"}'
```

### Bill teams

We can generate invoice for eLabFTW teams.

```shell
$ elapi bill-teams generate-invoice
```

We may just want to have a look at the billing information without generating invoice.

```shell
$ elapi bill-teams info -F yaml
```

We can also export this information as a `YAML` file to the export directory defined in configuration
file (`export_dir`).

```shell
elapi bill-teams info -F yaml --export
```

## Open-source

elAPI is open-source and published under AGPLv3 license. The repository is however hosted internally within
Universität Heidelberg's network. The codebase can still be accessed from [PyPI](https://pypi.org/project/elapi/#files).
If you express interest in having the repository made completely public, or if you have any question, feel free
to [contact us](mailto:elabftw@uni-heidelberg.de).