from src import LOG_FILE_PATH, APP_NAME, HOST, records, TOKEN_BEARER, DOWNLOAD_DIR, APP_DATA_DIR, TMP_DIR

detected_config_files = "\n- " + "\n- ".join(records.inspect_applied_config_files)
# print(detected_config_files)
info = f"""
## {APP_NAME} configuration information
The following debug information includes configuration values and their sources as detected by {APP_NAME}. 
> Name: Value ← Source

- **Log file path:** {LOG_FILE_PATH}
- **Host address:** {HOST} ← {records.inspect_applied_config["HOST"][1]}
- **API token:** ***** ← {records.inspect_applied_config["API_TOKEN"][1]}
- **Token bearer:** "{TOKEN_BEARER}"
- **Download directory:** {DOWNLOAD_DIR} ← {records.inspect_applied_config["DATA_DOWNLOAD_DIR"][1]}
- **App data directory:** {APP_DATA_DIR}
- **Caching directory:** {TMP_DIR}


**_Detected configuration files that are in use:_**
{detected_config_files}
"""
