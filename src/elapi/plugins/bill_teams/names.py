from dataclasses import dataclass

from ...configuration import KEY_PLUGIN_KEY_NAME

PLUGIN_NAME: str = "bill-teams"
PLUGIN_LINK: str = f"{KEY_PLUGIN_KEY_NAME}.{PLUGIN_NAME}".lower()
REGISTRY_SUB_PLUGIN_NAME: str = "registry"


# bill-teams plugin specific configuration
@dataclass
class BillingConfigKeys:
    plugin_name: str = PLUGIN_NAME.replace("-", "_")
    root_dir: str = "root_dir"


TARGET_GROUP_NAME: str = "teams"
TARGET_GROUP_NAME_SINGULAR: str = "team"
TARGET_GROUP_OWNER_NAME: str = "owners"
TARGET_GROUP_OWNER_NAME_SINGULAR: str = "owner"
