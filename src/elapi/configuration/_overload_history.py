from typing import Iterable, Optional, Tuple, Any

from ._config_history import FieldValueWithKey, AppliedConfigIdentity
from .config import history, FALLBACK_SOURCE_NAME
from .validators import MainConfigurationValidator
from ..core_validators import Validate, ValidationError, Exit


class ApplyConfigHistory:
    def __init__(self, configuration_fields: list[FieldValueWithKey]):
        from ._config_history import MinimalActiveConfiguration
        from .config import settings

        self.configuration_fields = configuration_fields
        self.active_configuration = MinimalActiveConfiguration()
        self.settings = settings

    @property
    def configuration_fields(self):
        return self._configuration_fields

    @configuration_fields.setter
    def configuration_fields(self, value):
        if not isinstance(value, Iterable) or isinstance(value, str):
            raise ValueError(
                f"Value must be an iterable of {FieldValueWithKey.__name__} namedtuple."
            )
        for tuple_ in value:
            if not isinstance(tuple_, FieldValueWithKey):
                raise ValueError(
                    f"'Value {tuple_}' is not a {FieldValueWithKey.__name__} namedtuple."
                )
        self._configuration_fields = value

    def _modify_history(self, key_name: str, value: str) -> None:
        _val, _src = self.active_configuration[key_name]
        self.active_configuration[key_name] = AppliedConfigIdentity(value, _src)
        if value != _val:
            try:
                history.delete(key_name)
            except KeyError:
                ...
            self.active_configuration[key_name] = AppliedConfigIdentity(
                value, FALLBACK_SOURCE_NAME
            )

    def apply(self) -> None:
        from ..loggers import Logger
        from .config import (
            KEY_API_TOKEN,
            KEY_EXPORT_DIR,
            KEY_UNSAFE_TOKEN_WARNING,
            KEY_ENABLE_HTTP2,
            KEY_VERIFY_SSL,
            KEY_TIMEOUT,
            KEY_DEVELOPMENT_MODE,
            KEY_PLUGIN_KEY_NAME,
            _XDG_DOWNLOAD_DIR,
            PROJECT_CONFIG_LOC,
            ENV_XDG_DOWNLOAD_DIR,
            FALLBACK_EXPORT_DIR,
            FALLBACK_SOURCE_NAME,
            CONFIG_FILE_NAME,
        )

        logger = Logger()

        for key_name, value in self.configuration_fields:
            if key_name == KEY_EXPORT_DIR:
                _val, _src = self.active_configuration[key_name]
                self.active_configuration[key_name] = AppliedConfigIdentity(
                    export_dir := value, _src
                )
                if export_dir == _XDG_DOWNLOAD_DIR:
                    try:
                        history.delete(key_name)
                    except KeyError:
                        ...
                    self.active_configuration[key_name] = AppliedConfigIdentity(
                        export_dir, ENV_XDG_DOWNLOAD_DIR
                    )
                elif export_dir == FALLBACK_EXPORT_DIR:
                    try:
                        history.delete(key_name)
                    except KeyError:
                        ...
                    self.active_configuration[key_name] = AppliedConfigIdentity(
                        export_dir, FALLBACK_SOURCE_NAME
                    )
            elif key_name == KEY_UNSAFE_TOKEN_WARNING:
                self._modify_history(key_name, unsafe_token_warning := value)
                if unsafe_token_warning and self.active_configuration[
                    KEY_API_TOKEN
                ].source == str(PROJECT_CONFIG_LOC):
                    logger.warning(
                        f"'{KEY_API_TOKEN}' field in project-based configuration file "
                        f"{PROJECT_CONFIG_LOC} found. This is highly discouraged. "
                        f"The token is at risk of being leaked into public repositories. "
                        f"If you still insist, please make sure {CONFIG_FILE_NAME} "
                        f"is included in .gitignore. You can disable this message by setting "
                        f"'{KEY_UNSAFE_TOKEN_WARNING.lower()}: False' in {CONFIG_FILE_NAME}."
                    )
            elif key_name in [
                KEY_ENABLE_HTTP2,
                KEY_VERIFY_SSL,
                KEY_TIMEOUT,
                KEY_DEVELOPMENT_MODE,
                KEY_PLUGIN_KEY_NAME,
            ]:
                self._modify_history(key_name, value)


def validate_configuration(limited_to: Optional[list]) -> None:
    try:
        validated_fields: list = Validate(
            MainConfigurationValidator(limited_to=limited_to)
        ).get()
    except ValidationError:
        raise Exit(1)
    else:
        for validator in limited_to:
            validator.ALREADY_VALIDATED = True
        if validated_fields:
            apply_settings = ApplyConfigHistory(validated_fields)
            apply_settings.apply()


def reinitiate_config(
    ignore_essential_validation: bool = False, ignore_already_validated: bool = False
) -> None:
    limited_to: Optional[list] = []
    if not ignore_essential_validation:
        if not ignore_already_validated:
            for validator in MainConfigurationValidator.ALL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = None
        validate_configuration(limited_to)
    else:
        if not ignore_already_validated:
            for validator in MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS
        validate_configuration(limited_to)


def preventive_missing_warning(field: Tuple[str, Any], /) -> None:
    from .._names import KEY_DEVELOPMENT_MODE
    from ..styles import Missing
    from ..utils import get_sub_package_name, PreventiveWarning

    configuration_sub_package_name = get_sub_package_name(__package__)
    if not isinstance(field, Iterable) and not isinstance(field, str):
        raise TypeError(
            f"{preventive_missing_warning.__name__} only accepts an iterable of key-value pair."
        )
    try:
        key, value = field
    except ValueError as e:
        raise ValueError(
            "Only a pair of configuration key and its value in an "
            f"iterable can be passed to {preventive_missing_warning.__name__}."
        ) from e
    if isinstance(value, Missing):
        key = key.lower()
        raise PreventiveWarning(
            f"Value for '{key}' from configuration file is missing. "
            f"This is not necessarily a critical error but a future operation might fail. "
            f"If '{key}' is supposed to fallback to a default value or if you want to "
            f"get a more precise error message, make sure to run function "
            f"'{reinitiate_config.__name__}()' (can be imported with "
            f"'from {configuration_sub_package_name} import {reinitiate_config.__name__}') "
            f"before running anything else. You could also just define a valid value for '{key}' "
            f"in configuration file. This warning may also be shown because '{KEY_DEVELOPMENT_MODE.lower()}' "
            f"is set to '{True}' in configuration file. In most cases, just running "
            f"'{reinitiate_config.__name__}()' should fix this issue."
        )
