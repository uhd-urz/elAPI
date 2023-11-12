from ..configuration import (
    APP_NAME,
    inspect,
    UNSAFE_TOKEN_WARNING,
    EXPORT_DIR,
    APP_DATA_DIR,
    TMP_DIR,
    KEY_HOST,
    KEY_API_TOKEN,
    KEY_UNSAFE_TOKEN_WARNING,
    KEY_EXPORT_DIR,
    LOG_FILE_PATH,
)

from ..styles import Missing, ColorText
from ..styles.colors import RED, BLUE, YELLOW, LIGHTGREEN

detected_config = inspect.applied_config
detected_config_files = inspect.applied_config_files
FALLBACK = "DEFAULT"
missing = ColorText(Missing())

try:
    api_token_masked = detected_config[KEY_API_TOKEN].value or "''"
    api_token_source = detected_config_files[detected_config[KEY_API_TOKEN].source]
except KeyError:
    api_token_masked, api_token_source = missing, None

try:
    unsafe_token_use_source = detected_config[KEY_UNSAFE_TOKEN_WARNING].source
    unsafe_token_use_source = detected_config_files[unsafe_token_use_source]
except KeyError:
    unsafe_token_use_source = FALLBACK
finally:
    unsafe_token_use_value = "Yes" if UNSAFE_TOKEN_WARNING else "No"

try:
    host_value = detected_config[KEY_HOST].value or "''"
    host_source = detected_config_files[detected_config[KEY_HOST].source]
except KeyError:
    host_value, host_source = missing, None

try:
    export_dir_source = detected_config_files[detected_config[KEY_EXPORT_DIR].source]
except KeyError:
    export_dir_source = FALLBACK


detected_config_files_formatted = "\n- " + "\n- ".join(
    f"`{v}`: {k}" for k, v in detected_config_files.items()
)


def show(show_keys: bool) -> str:
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
                if show_keys
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
                if show_keys
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
            if show_keys
            else ""
        )
        + f": {EXPORT_DIR} ← `{export_dir_source}`"
        + f"""
- {ColorText('App data directory').colorize(LIGHTGREEN)}: {APP_DATA_DIR}
- {ColorText('Caching directory').colorize(LIGHTGREEN)}: {TMP_DIR}
"""
        + "\n"
        + f"- {ColorText('Unsafe API token use warning').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_UNSAFE_TOKEN_WARNING.lower()).colorize(YELLOW)}]**"
            if show_keys
            else ""
        )
        + f": {unsafe_token_use_value} ← `{unsafe_token_use_source}`"
        + f"""


{ColorText("Detected configuration files that are in use:").colorize(BLUE)}
{detected_config_files_formatted}
"""
        + (
            f"""
- `{FALLBACK}`: Fallback value for when no user configuration is found.
"""
            if FALLBACK in (export_dir_source, unsafe_token_use_source)
            else ""
        )
    )

    return _info
