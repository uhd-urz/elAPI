from pathlib import Path
from typing import Optional

from ..styles import Missing
from ._overload_history import reinitiate_config
from .config import (
    KEY_API_TOKEN,
    KEY_ASYNC_CAPACITY,
    KEY_ASYNC_RATE_LIMIT,
    KEY_DEVELOPMENT_MODE,
    KEY_ENABLE_HTTP2,
    KEY_EXPORT_DIR,
    KEY_HOST,
    KEY_PLUGIN_KEY_NAME,
    KEY_TIMEOUT,
    KEY_UNSAFE_TOKEN_WARNING,
    KEY_VERIFY_SSL,
    APIToken,
    MinimalActiveConfiguration,
)


def get_active_host(*, skip_validation: bool = False) -> str:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_HOST)


def get_active_api_token(*, skip_validation: bool = False) -> APIToken:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_API_TOKEN)


def get_active_export_dir(*, skip_validation: bool = False) -> Path:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_EXPORT_DIR)


def get_active_unsafe_token_warning(*, skip_validation: bool = False) -> bool:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_UNSAFE_TOKEN_WARNING)


def get_active_enable_http2(*, skip_validation: bool = False) -> bool:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_ENABLE_HTTP2)


def get_active_verify_ssl(*, skip_validation: bool = False) -> bool:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_VERIFY_SSL)


def get_active_timeout(*, skip_validation: bool = False) -> float:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_TIMEOUT)


def get_active_async_rate_limit(*, skip_validation: bool = False) -> Optional[int]:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_ASYNC_RATE_LIMIT)


def get_active_async_capacity(*, skip_validation: bool = False) -> Optional[int]:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_ASYNC_CAPACITY)


def _development_mode_validation_switch() -> None:
    _value = MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)
    if _value is False or _value == Missing():
        reinitiate_config()


def get_development_mode(*, skip_validation: bool = False) -> bool:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)


def get_active_plugin_configs(*, skip_validation: bool = False) -> dict:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_PLUGIN_KEY_NAME)
