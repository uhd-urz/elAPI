# elabftw API client extension

This package adds functionalities we need to manage [`elabftw`](https://github.com/elabftw/elabftw/) usage at the
Heidelberg
University.

## Development environment

To get started with the development of this extension, you need to
install [Poetry](https://python-poetry.org/docs/#installation). Poetry utilizes `pyproject.toml` as suggested
by [`PEP 518`](https://peps.python.org/pep-0518/).

1. Install Poetry.
2. Clone this repository to a preferred directory (e.g., `~/elabftw`). `cd` to `~/elabftw`.
3. Run `poetry config virtualenvs.in-project --local true`. This will allow Poetry to install virtual environment in the
   current directory, inside of `.venv`. This is necessary **for now** for one of the experimental CLI programs.
4. Run `poetry shell`. This will initialize and automatically activate the virtual environment. Makes sure the virtual
   environment is created
   inside `./.venv`! See `poetry env info`.
5. Run `poetry install`. This will install all the necessary dependencies.
6. `elabftw-get` supports the following configuration locations:
    - `/etc/elabftw-get.yaml` <- Lowest precedence
    - `$HOME/.config/elabftw-get.yaml`
    - `<project directory of elabftw-get (this repository)>/elabftw-get.yaml` <- highest precedence

   `elabftw-get` expects to parse necessary authentication information from the `elabftw-get.yaml`.
   ```yaml
   
   # elabftw-get.yaml example
   ---
   host: "https://elabftw-dev.uni-heidelberg.de/api/v2"
   api_token: "<your api token>"
   unsafe_api_token_warning: true
   # when true elabftw-get will show warning if api_token is included in the project-level configuration file
   download_dir: "~/Downloads"  
   # elabftw-get uses /var/tmp/elabftw-get to store response data from back from API requests. However, a user may wish to use those data and have them saved somewhere else. This field defines an export path for that purpose.  
   ```

7. Restart virtual environment for the changes to take effect.
   ```bash
   $ exit
   $ poetry shell
   Spawning shell within ./elabftw/.venv ...
   ```

## elabftw-get CLI

`elabftw-get` also provides a CLI program for ease of making common requests. It needs to added to one of your
paths.

```bash
$ export PYTHONPATH=".:$PYTHONPATH"
$ ln -s <path to project directory>/cli/elabftw_get.py  ~/.local/bin/elabftw-get
```

Run `elabftw_get --help` to see the supported options. Exporting `PYTHONPATH=".:$PYTHONPATH"` will not be necessary for
the final production version.

## Apps

`./apps` are where programs with business logic reside. `apps/bill_teams.py` generates a dictionary that contains
information about active team owners. To run an app from the command line, first make sure your working directory
is `<path to project directory>`, and Poetry virtual environment is activated (`poetry shell`). Then run:

```sh
# python -m apps.<app name> 
# Example:
python -m apps.bill_teams 
```

Activating a virtual environment will not be necessary for the final production-ready version.