from pathlib import Path
from typing import Union

from ._overload_history import reinitiate_config
from .config import APIToken
from ..styles import Missing


def _run_validation_once() -> None:
    if get_development_mode() is False or get_development_mode() == Missing():
        reinitiate_config()


def get_active_host() -> str:
    from .config import KEY_HOST, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_HOST)


def get_active_host_url_without_api_subdir() -> Union[str, Missing]:
    import re
    from .config import ELAB_HOST_URL_API_SUFFIX

    if (host := get_active_host()) != Missing():
        return re.sub(
            ELAB_HOST_URL_API_SUFFIX,
            r"",
            get_active_host(),
            count=1,
            flags=re.IGNORECASE,
        )
    return host


def get_active_api_token() -> APIToken:
    from .config import KEY_API_TOKEN, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_API_TOKEN)


def get_active_export_dir() -> Path:
    from .config import KEY_EXPORT_DIR, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_EXPORT_DIR)


def get_active_unsafe_token_warning() -> bool:
    from .config import KEY_UNSAFE_TOKEN_WARNING, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_UNSAFE_TOKEN_WARNING)


def get_active_enable_http2() -> bool:
    from .config import KEY_ENABLE_HTTP2, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_ENABLE_HTTP2)


def get_active_verify_ssl() -> bool:
    from .config import KEY_VERIFY_SSL, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_VERIFY_SSL)


def get_active_timeout() -> float:
    from .config import KEY_TIMEOUT, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_TIMEOUT)


def get_development_mode() -> bool:
    from .config import KEY_DEVELOPMENT_MODE, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)


def get_active_plugin_configs() -> dict:
    from .config import KEY_PLUGIN_KEY_NAME, MinimalActiveConfiguration

    _run_validation_once()
    return MinimalActiveConfiguration().get_value(KEY_PLUGIN_KEY_NAME)
