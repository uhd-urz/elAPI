from src import LOG_FILE_PATH, APP_NAME, HOST, records, TOKEN_BEARER, DOWNLOAD_DIR, APP_DATA_DIR, TMP_DIR

api_token_masked, api_token_source = records.inspect_applied_config["API_TOKEN_MASKED"]
unsafe_token_use_value, unsafe_token_use_source = records.inspect_applied_config["UNSAFE_API_TOKEN_WARNING"]
unsafe_token_use_value = "Yes" if records.inspect_applied_config["API_TOKEN"] else "No"
host_source = records.inspect_applied_config["HOST"][1]
download_dir_source = records.inspect_applied_config["DOWNLOAD_DIR"][1]
detected_config_files = "\n- " + "\n- ".join(records.inspect_applied_config_files)

info = f"""
## {APP_NAME} configuration information
The following debug information includes configuration values and their sources as detected by {APP_NAME}. 
> Name: Value ← Source

- **Log file path:** {LOG_FILE_PATH}
- **Host address:** {HOST} ← {host_source}
- **API token:** {api_token_masked} ← {api_token_source}
- **Token bearer:** "{TOKEN_BEARER}"
- **Download directory:** {DOWNLOAD_DIR} ← {download_dir_source}
- **App data directory:** {APP_DATA_DIR}
- **Caching directory:** {TMP_DIR}
- **Unsafe API token use warning:** {unsafe_token_use_value} ← {unsafe_token_use_source}


**_Detected configuration files that are in use:_**
{detected_config_files}
"""
