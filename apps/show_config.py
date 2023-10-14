from cli import Missing
from src.config import (APP_NAME, inspect, UNSAFE_TOKEN_WARNING, EXPORT_DIR, APP_DATA_DIR,
                        TMP_DIR, CLEANUP_AFTER, KEY_HOST, KEY_API_TOKEN, KEY_UNSAFE_TOKEN_WARNING,
                        KEY_EXPORT_DIR, KEY_CLEANUP)
from src.log_file import LOG_FILE_PATH

detected_config = inspect.applied_config
detected_config_files = inspect.applied_config_files
FALLBACK = "DEFAULT"

try:
    api_token_masked = detected_config[KEY_API_TOKEN].value or "''"
    api_token_source = detected_config_files[detected_config[KEY_API_TOKEN].source]
except KeyError:
    api_token_masked, api_token_source = Missing(), None

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
    host_value, host_source = Missing(), None

try:
    export_dir_source = detected_config_files[detected_config[KEY_EXPORT_DIR].source]
except KeyError:
    export_dir_source = FALLBACK

try:
    cleanup_source = detected_config_files[detected_config[KEY_CLEANUP].source]
except KeyError:
    cleanup_source = FALLBACK
finally:
    cleanup_value = "Yes" if CLEANUP_AFTER else "No"

detected_config_files_formatted = "\n- " + "\n- ".join(f"`{v}`: {k}" for k, v in detected_config_files.items())

info = (f"""
## {APP_NAME} configuration information
The following debug information includes configuration values and their sources as detected by {APP_NAME}. 
> Name: Value ← Source

- **Log file path:** {LOG_FILE_PATH}
""" + (f"""
- **Host address:** {host_value} ← `{host_source}`
""" if host_source else f"- **Host address:** _{host_value.colorize()}_\n") + (f"""
- **API token:** {api_token_masked} ← `{api_token_source}`
""" if api_token_source else f"- **API token:** _{api_token_masked.colorize()}_") + f"""
- **Export directory:** {EXPORT_DIR} ← `{export_dir_source}`
- **App data directory:** {APP_DATA_DIR}
- **Caching directory:** {TMP_DIR}
- **Unsafe API token use warning:** {unsafe_token_use_value} ← 
`{unsafe_token_use_source}`
- **Cleanup cache after finishing task:** {cleanup_value} ← 
`{cleanup_source}`


**_Detected configuration files that are in use:_**
{detected_config_files_formatted}
""" + (f"""
- `{FALLBACK}`: Fallback value for when no user configuration is found.
""" if FALLBACK in (export_dir_source, unsafe_token_use_source, cleanup_source) else ""))
