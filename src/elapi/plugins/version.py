from ..configuration import APP_NAME
from ..path import ProperPath


def elapi_version() -> str:
    with ProperPath(f"{__file__}/../../VERSION").open() as version_file:
        _read_version = version_file.read().strip()
    APP_VERSION = _read_version

    return f"{APP_NAME} {APP_VERSION}"
