from pathlib import Path

from ...configuration import (
    CONFIG_FILE_NAME,
    ConfigurationValidation,
    get_active_plugin_configs,
)
from ...core_validators import CriticalValidationError, Validate, Validator
from ...loggers import Logger
from ...path import ProperPath
from .names import PLUGIN_LINK, BillingConfigKeys

logger = Logger()
billing_config_keys = BillingConfigKeys()


class RootDirConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self):
        bill_teams_plugin_config: dict = get_active_plugin_configs().get(
            billing_config_keys.plugin_name, dict()
        )
        super().__init__(bill_teams_plugin_config)

    def validate(self) -> Path:
        try:
            root_dir = self.active_configuration[billing_config_keys.root_dir]
        except KeyError as e:
            logger.error(
                f"Key '{billing_config_keys.root_dir}' does not exist under "
                f"plugin configuration '{PLUGIN_LINK}' in configuration "
                f"file {CONFIG_FILE_NAME}."
            )
            raise CriticalValidationError from e
        else:
            try:
                root_dir = ProperPath(root_dir)
            except ValueError as e:
                logger.error(
                    f"'{PLUGIN_LINK}.{billing_config_keys.root_dir}' value '{root_dir}' "
                    f"found in configuration file is an invalid path value."
                )
                raise CriticalValidationError from e
            else:
                if not root_dir.kind == "dir":
                    logger.error(
                        f"'{PLUGIN_LINK}.{billing_config_keys.root_dir}' value '{root_dir}' "
                        f"found in configuration file is not a directory path."
                    )
                    raise CriticalValidationError
                root_dir = root_dir.expanded
                return root_dir


def get_root_dir() -> Path:
    return Validate(RootDirConfigurationValidator()).get()
