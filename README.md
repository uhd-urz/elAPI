# elabftw API client extension

This package adds functionalities we need to manage our researchers' at the heidelberg
University [`elabftw`](https://github.com/elabftw/elabftw/) usage.

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
6. Create a `.env` file on the root directory `~/elabftw`. Add the following key-value pairs:
   ```bash
   API_KEY="<your API token>"
   TOKEN_BEARER="Authorization"
   # avoid "...api/v2/". use "...api/v2"
   HOST="https://elabftw-dev.uni-heidelberg.de/api/v2"
   ```
   **Important:** `.env` file support will soon be deprecated in favor of more Linux-conventional configuration files.
7. Restart virtual environment for the changes to take effect.
   ```bash
   $ exit
   $ poetry shell
   Spawning shell within ./elabftw/.venv ...
   ```
   