from pathlib import Path

from .config import APIToken


def get_active_host() -> str:
    from .config import KEY_HOST, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_HOST)


def get_active_api_token() -> APIToken:
    from .config import KEY_API_TOKEN, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_API_TOKEN)


def get_active_export_dir() -> Path:
    from .config import KEY_EXPORT_DIR, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_EXPORT_DIR)


def get_active_unsafe_token_warning() -> bool:
    from .config import KEY_UNSAFE_TOKEN_WARNING, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_UNSAFE_TOKEN_WARNING)


def get_active_enable_http2() -> bool:
    from .config import KEY_ENABLE_HTTP2, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_ENABLE_HTTP2)


def get_active_verify_ssl() -> bool:
    from .config import KEY_VERIFY_SSL, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_VERIFY_SSL)


def get_active_timeout() -> float:
    from .config import KEY_TIMEOUT, MinimalActiveConfiguration

    return MinimalActiveConfiguration().get_value(KEY_TIMEOUT)
