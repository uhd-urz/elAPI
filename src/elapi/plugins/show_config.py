from .._names import ENV_XDG_DOWNLOAD_DIR
from ..configuration import (
    APP_NAME,
    APP_BRAND_NAME,
    inspect,
    get_active_unsafe_token_warning,
    get_active_enable_http2,
    get_active_export_dir,
    get_active_verify_ssl,
    get_active_timeout,
    get_development_mode,
    APP_DATA_DIR,
    TMP_DIR,
    KEY_HOST,
    KEY_API_TOKEN,
    KEY_UNSAFE_TOKEN_WARNING,
    KEY_ENABLE_HTTP2,
    KEY_VERIFY_SSL,
    KEY_TIMEOUT,
    KEY_DEVELOPMENT_MODE,
    KEY_EXPORT_DIR,
    LOG_FILE_PATH,
    EXTERNAL_LOCAL_PLUGIN_DIR,
    FALLBACK_SOURCE_NAME,
    minimal_active_configuration,
)

# noinspection PyProtectedMember
from ..configuration.config import (
    _CANON_CONFIG_FILE_NAME,
    CONFIG_MIS_PATH,
    CANON_YAML_EXTENSION,
    CONFIG_FILE_EXTENSION,
)
from ..styles import Missing, ColorText
from ..styles.colors import RED, BLUE, YELLOW, LIGHTGREEN, LIGHTCYAN

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
    unsafe_token_use_value = "True" if get_active_unsafe_token_warning() else "False"

try:
    enable_http2_source = detected_config[KEY_ENABLE_HTTP2].source
    enable_http2_source = detected_config_files[enable_http2_source]
except KeyError:
    enable_http2_source = FALLBACK_SOURCE_NAME
finally:
    enable_http2_value = "True" if get_active_enable_http2() else "False"


try:
    verify_ssl_source = detected_config[KEY_VERIFY_SSL].source
    verify_ssl_source = detected_config_files[verify_ssl_source]
except KeyError:
    verify_ssl_source = FALLBACK_SOURCE_NAME
finally:
    verify_ssl_value = "True" if get_active_verify_ssl() else "False"


try:
    timeout_source = detected_config[KEY_TIMEOUT].source
    timeout_source = detected_config_files[timeout_source]
except KeyError:
    timeout_source = FALLBACK_SOURCE_NAME
finally:
    timeout_value = get_active_timeout()
    timeout_value = f"{timeout_value} " + ("seconds" if timeout_value > 1 else "second")


try:
    development_mode_source = detected_config[KEY_DEVELOPMENT_MODE].source
    development_mode_source = detected_config_files[development_mode_source]
except KeyError:
    development_mode_source = FALLBACK_SOURCE_NAME
finally:
    development_mode_value = "True" if get_development_mode() else "False"


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

wrong_ext_warning = (
    f"File '{_CANON_CONFIG_FILE_NAME}' detected in location '{CONFIG_MIS_PATH}'. "
    f"If it is meant to be an {APP_NAME} configuration file, "
    f"please rename the file extension from '{CANON_YAML_EXTENSION}' "
    f"to '{CONFIG_FILE_EXTENSION}'. {APP_NAME} only supports '{CONFIG_FILE_EXTENSION}' "
    f"as file extension for configuration files."
)


def show(no_keys: bool) -> str:
    _info = (
        f"""
## {APP_BRAND_NAME} configuration information
The following information includes configuration values and their sources as detected by {APP_NAME}. 
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
- {ColorText('Third-party plugins directory').colorize(LIGHTCYAN)}: {EXTERNAL_LOCAL_PLUGIN_DIR}
- {ColorText('Caching directory').colorize(LIGHTGREEN)}: {TMP_DIR if not isinstance(TMP_DIR, Missing) else 
    f'_{ColorText(TMP_DIR).colorize(RED)}_'}
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
        + "\n"
        + f"- {ColorText('Development mode').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_DEVELOPMENT_MODE.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {development_mode_value} ← `{development_mode_source}`"
        + f"""


{ColorText("Detected configuration sources that are in use:").colorize(BLUE)}
{detected_config_files_formatted}
"""
        + (
            f"""
- `{FALLBACK_SOURCE_NAME}`: Fallback value for when no user configuration is found or found to be invalid.
"""
            if FALLBACK_SOURCE_NAME
            in (
                export_dir_source,
                unsafe_token_use_source,
                enable_http2_source,
                verify_ssl_source,
                development_mode_source,
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
        + (
            f"""


**{ColorText("Attention:").colorize(RED)}**
    {wrong_ext_warning}
    """
            if CONFIG_MIS_PATH is not None
            else ""
        )
    )

    return _info
