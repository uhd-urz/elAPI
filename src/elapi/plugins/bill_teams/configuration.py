from pathlib import Path

from .names import CONFIG_PLUGIN_NAME, PLUGIN_LINK, CONFIG_KEY_ROOT_DIR
from ...configuration import get_active_plugin_configs, CONFIG_FILE_NAME, ConfigurationValidation
from ...core_validators import Validator, Validate, CriticalValidationError
from ...loggers import Logger
from ...path import ProperPath

logger = Logger()

bill_teams_plugin_config: dict = get_active_plugin_configs().get(
    CONFIG_PLUGIN_NAME, dict()
)


class RootDirConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self):
        super().__init__(bill_teams_plugin_config)

    def validate(self) -> Path:
        try:
            root_dir = self.active_configuration[CONFIG_KEY_ROOT_DIR]
        except KeyError as e:
            logger.error(
                f"Key '{CONFIG_KEY_ROOT_DIR}' does not exist under "
                f"plugin configuration '{PLUGIN_LINK}' in configuration "
                f"file {CONFIG_FILE_NAME}."
            )
            raise CriticalValidationError from e
        else:
            try:
                root_dir = ProperPath(root_dir)
            except ValueError as e:
                logger.error(
                    f"'{PLUGIN_LINK}.{CONFIG_KEY_ROOT_DIR}' value '{root_dir}' "
                    f"found in configuration file is an invalid path value."
                )
                raise CriticalValidationError from e
            else:
                if not root_dir.kind == "dir":
                    logger.error(
                        f"'{PLUGIN_LINK}.{CONFIG_KEY_ROOT_DIR}' value '{root_dir}' "
                        f"found in configuration file is not a directory path."
                    )
                    raise CriticalValidationError
                root_dir = root_dir.expanded
                return root_dir


def get_root_dir() -> Path:
    return Validate(RootDirConfigurationValidator()).get()
