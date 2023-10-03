from cli import Missing
from src.log_file import LOG_FILE_PATH
from src.config import (APP_NAME, records, TOKEN_BEARER, UNSAFE_TOKEN_WARNING, EXPORT_DIR, APP_DATA_DIR,
                        TMP_DIR, CLEANUP_AFTER)
from src.path import ProperPath

detected_config = records.inspect_applied_config
detected_config_files = records.inspect_applied_config_files
FALLBACK = "DEFAULT"

try:
    api_token_masked, api_token_source = detected_config["API_TOKEN_MASKED"]
    api_token_source = detected_config_files[api_token_source]
except KeyError:
    api_token_masked, api_token_source = Missing(), None

try:
    unsafe_token_use_source = detected_config["UNSAFE_API_TOKEN_WARNING"][1]
    unsafe_token_use_source = detected_config_files[unsafe_token_use_source]
except KeyError:
    unsafe_token_use_source = FALLBACK
finally:
    unsafe_token_use_value = "Yes" if UNSAFE_TOKEN_WARNING else "No"

try:
    host_value = detected_config["HOST"][0]
    host_source = detected_config_files[detected_config["HOST"][1]]
except KeyError:
    host_value, host_source = Missing(), None

try:
    export_dir_source = detected_config_files[detected_config["EXPORT_DIR"][1]]
except KeyError:
    export_dir_source = FALLBACK
else:
    # TODO: The following needs to refactored so ProperPath needs not to be applied again!
    if ProperPath(export_dir_value := detected_config["EXPORT_DIR"][0]).expanded.resolve() != EXPORT_DIR:
        export_dir_source = FALLBACK

try:
    cleanup_source = detected_config_files[detected_config["CLEANUP_AFTER_FINISH"][1]]
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
- **Token bearer:** {TOKEN_BEARER}
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
