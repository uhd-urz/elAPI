from dataclasses import dataclass

from src import (LOG_FILE_PATH, APP_NAME, records, TOKEN_BEARER, UNSAFE_TOKEN_WARNING, DOWNLOAD_DIR, APP_DATA_DIR,
                 TMP_DIR, CLEANUP_AFTER)

detected_config = records.inspect_applied_config
detected_config_files = records.inspect_applied_config_files
FALLBACK = "DEFAULT"


@dataclass(slots=True, eq=False)
class Missing:
    message: str = "MISSING"

    def __str__(self):
        return self.message

    def __eq__(self, other):
        if not other or isinstance(other, Missing):
            return True

    def __bool__(self):
        return False


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
    download_dir_source = detected_config_files[detected_config["DOWNLOAD_DIR"][1]]
except KeyError:
    download_dir_source = FALLBACK

try:
    cleanup_source = detected_config_files[detected_config["CLEANUP_AFTER_FINISH"][1]]
except KeyError:
    cleanup_source = FALLBACK
finally:
    cleanup_value = "True" if CLEANUP_AFTER else "False"

detected_config_files_formatted = "\n- " + "\n- ".join(f"`{v}`: {k}" for k, v in detected_config_files.items())

info = (f"""
## {APP_NAME} configuration information
The following debug information includes configuration values and their sources as detected by {APP_NAME}. 
> Name: Value ← Source

- **Log file path:** {LOG_FILE_PATH}
""" + (f"""
- **Host address:** {host_value} ← `{host_source}`
""" if host_source else f"- **Host address:** _{host_value}_\n") + (f"""
- **API token:** {api_token_masked} ← `{api_token_source}`
""" if api_token_source else f"- **API token:** _{api_token_masked}_") + f"""
- **Token bearer:** {TOKEN_BEARER}
- **Download directory:** {DOWNLOAD_DIR} ← `{download_dir_source}`
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
""" if FALLBACK in (download_dir_source, unsafe_token_use_source, cleanup_source) else ""))
