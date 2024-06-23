from .._names import ENV_XDG_DOWNLOAD_DIR
from ..configuration import (
    APP_NAME,
    inspect,
    get_active_unsafe_token_warning,
    get_active_enable_http2,
    get_active_export_dir,
    get_active_verify_ssl,
    get_active_timeout,
    APP_DATA_DIR,
    TMP_DIR,
    KEY_HOST,
    KEY_API_TOKEN,
    KEY_UNSAFE_TOKEN_WARNING,
    KEY_ENABLE_HTTP2,
    KEY_VERIFY_SSL,
    KEY_TIMEOUT,
    KEY_EXPORT_DIR,
    LOG_FILE_PATH,
    FALLBACK_SOURCE_NAME,
    minimal_active_configuration,
)
from ..styles import Missing, ColorText
from ..styles.colors import RED, BLUE, YELLOW, LIGHTGREEN

detected_config = minimal_active_configuration
detected_config_files = inspect.applied_config_files
missing = ColorText(Missing())

try:
    api_token_masked = detected_config[KEY_API_TOKEN].value or "''"
    api_token_masked = "''" if api_token_masked == "" else api_token_masked
    api_token_source = detected_config_files[detected_config[KEY_API_TOKEN].source]
except KeyError:
    api_token_masked, api_token_source = missing, None

try:
    unsafe_token_use_source = detected_config[KEY_UNSAFE_TOKEN_WARNING].source
    unsafe_token_use_source = detected_config_files[unsafe_token_use_source]
except KeyError:
    unsafe_token_use_source = FALLBACK_SOURCE_NAME
finally:
    unsafe_token_use_value = "Yes" if get_active_unsafe_token_warning() else "No"

try:
    enable_http2_source = detected_config[KEY_ENABLE_HTTP2].source
    enable_http2_source = detected_config_files[enable_http2_source]
except KeyError:
    enable_http2_source = FALLBACK_SOURCE_NAME
finally:
    enable_http2_value = "Yes" if get_active_enable_http2() else "No"


try:
    verify_ssl_source = detected_config[KEY_VERIFY_SSL].source
    verify_ssl_source = detected_config_files[verify_ssl_source]
except KeyError:
    verify_ssl_source = FALLBACK_SOURCE_NAME
finally:
    verify_ssl_value = "Yes" if get_active_verify_ssl() else "No"


try:
    timeout_source = detected_config[KEY_TIMEOUT].source
    timeout_source = detected_config_files[timeout_source]
except KeyError:
    timeout_source = FALLBACK_SOURCE_NAME
finally:
    timeout_value = get_active_timeout()
    timeout_value = f"{timeout_value} " + ("seconds" if timeout_value > 1 else "second")


try:
    host_value = detected_config[KEY_HOST].value
    host_value = "''" if host_value == "" else host_value
    host_source = detected_config_files[detected_config[KEY_HOST].source]
except KeyError:
    host_value, host_source = missing, None

try:
    export_dir_source = detected_config_files[detected_config[KEY_EXPORT_DIR].source]
except KeyError:
    export_dir_source = detected_config[KEY_EXPORT_DIR].source


detected_config_files_formatted = "\n- " + "\n- ".join(
    f"`{v}`: {k}" for k, v in detected_config_files.items()
)


def show(no_keys: bool) -> str:
    _info = (
        f"""
## {APP_NAME} configuration information
The following debug information includes configuration values and their sources as detected by {APP_NAME}. 
> Name [Key]: Value ← Source

- {ColorText('Log file path').colorize(LIGHTGREEN)}: {LOG_FILE_PATH}
"""
        + (
            f"- {ColorText('Host address').colorize(LIGHTGREEN)}"
            + (
                f" **[{ColorText(KEY_HOST.lower()).colorize(YELLOW)}]**"
                if not no_keys
                else ""
            )
            + ":"
            + (
                f" {host_value} ← `{host_source}`"
                if host_source
                else f" _{host_value.colorize(RED)}_\n"
            )
        )
        + "\n"
        + (
            f"- {ColorText('API Token').colorize(LIGHTGREEN)}"
            + (
                f" **[{ColorText(KEY_API_TOKEN.lower()).colorize(YELLOW)}]**"
                if not no_keys
                else ""
            )
            + ":"
            + (
                f" {api_token_masked} ← `{api_token_source}`"
                if api_token_source
                else f" _{api_token_masked.colorize(RED)}_\n"
            )
        )
        + "\n"
        + f"- {ColorText('Export directory').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_EXPORT_DIR.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {get_active_export_dir()} ← `{export_dir_source}`"
        + f"""
- {ColorText('App data directory').colorize(LIGHTGREEN)}: {APP_DATA_DIR}
- {ColorText('Caching directory').colorize(LIGHTGREEN)}: {TMP_DIR}
"""
        + "\n"
        + f"- {ColorText('Unsafe API token use warning').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_UNSAFE_TOKEN_WARNING.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {unsafe_token_use_value} ← `{unsafe_token_use_source}`"
        + "\n"
        + f"- {ColorText('Enable HTTP/2').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_ENABLE_HTTP2.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {enable_http2_value} ← `{enable_http2_source}`"
        + "\n"
        + f"- {ColorText('Verify SSL certificate').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_VERIFY_SSL.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {verify_ssl_value} ← `{verify_ssl_source}`"
        + "\n"
        + f"- {ColorText('Timeout duration').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_TIMEOUT.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {timeout_value} ← `{timeout_source}`"
        + f"""


{ColorText("Detected configuration sources that are in use:").colorize(BLUE)}
{detected_config_files_formatted}
"""
        + (
            f"""
- `{FALLBACK_SOURCE_NAME}`: Fallback value for when no user configuration is found.
"""
            if FALLBACK_SOURCE_NAME
            in (
                export_dir_source,
                unsafe_token_use_source,
                enable_http2_source,
                verify_ssl_source,
            )
            else ""
        )
        + (
            f"""
- `{ENV_XDG_DOWNLOAD_DIR}`: Environment variable.
"""
            if ENV_XDG_DOWNLOAD_DIR in (export_dir_source,)
            else ""
        )
    )

    return _info
