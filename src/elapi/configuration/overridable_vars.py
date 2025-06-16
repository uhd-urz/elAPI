from pathlib import Path
from typing import Union

from ._overload_history import reinitiate_config
from .config import APIToken
from ..styles import Missing


def get_active_host(*, skip_validation: bool = False) -> str:
    from .config import KEY_HOST, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_HOST)


def get_active_host_url_without_api_subdir(
    *, skip_validation: bool = False
) -> Union[str, Missing]:
    import re
    from .config import ELAB_HOST_URL_API_SUFFIX

    if (host := get_active_host(skip_validation=skip_validation)) != Missing():
        return re.sub(
            ELAB_HOST_URL_API_SUFFIX,
            r"",
            get_active_host(skip_validation=skip_validation),
            count=1,
            flags=re.IGNORECASE,
        )
    return host


def get_active_api_token(*, skip_validation: bool = False) -> APIToken:
    from .config import KEY_API_TOKEN, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_API_TOKEN)


def get_active_export_dir(*, skip_validation: bool = False) -> Path:
    from .config import KEY_EXPORT_DIR, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_EXPORT_DIR)


def get_active_unsafe_token_warning(*, skip_validation: bool = False) -> bool:
    from .config import KEY_UNSAFE_TOKEN_WARNING, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_UNSAFE_TOKEN_WARNING)


def get_active_enable_http2(*, skip_validation: bool = False) -> bool:
    from .config import KEY_ENABLE_HTTP2, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_ENABLE_HTTP2)


def get_active_verify_ssl(*, skip_validation: bool = False) -> bool:
    from .config import KEY_VERIFY_SSL, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_VERIFY_SSL)


def get_active_timeout(*, skip_validation: bool = False) -> float:
    from .config import KEY_TIMEOUT, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_TIMEOUT)


def _development_mode_validation_switch():
    from .config import KEY_DEVELOPMENT_MODE, MinimalActiveConfiguration

    _value = MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)
    if _value is False or _value == Missing():
        reinitiate_config()


def get_development_mode(*, skip_validation: bool = False) -> bool:
    from .config import KEY_DEVELOPMENT_MODE, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)


def get_active_plugin_configs(*, skip_validation: bool = False) -> dict:
    from .config import KEY_PLUGIN_KEY_NAME, MinimalActiveConfiguration

    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_PLUGIN_KEY_NAME)
