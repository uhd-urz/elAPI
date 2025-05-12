from ...configuration import KEY_PLUGIN_KEY_NAME

PLUGIN_NAME: str = "bill-teams"
PLUGIN_LINK: str = f"{KEY_PLUGIN_KEY_NAME}.{PLUGIN_NAME}".lower()
REGISTRY_SUB_PLUGIN_NAME: str = "registry"
# bill-teams plugin specific configuration
CONFIG_PLUGIN_NAME: str = PLUGIN_NAME.replace("-", "_")
CONFIG_KEY_ROOT_DIR: str = "root_dir"
CONFIG_KEY_MAX_CONNECTIONS: str = "max_connections"
CONFIG_KEY_MAX_KEEPALIVE_CONNECTIONS: str = "max_keepalive_connections"
TARGET_GROUP_NAME: str = "teams"
TARGET_GROUP_NAME_SINGULAR: str = "team"
TARGET_GROUP_OWNER_NAME: str = "owners"
TARGET_GROUP_OWNER_NAME_SINGULAR: str = "owner"
