from typing import Iterable, Optional

from ._config_history import FieldValueWithKey, AppliedConfigIdentity
from .config import history, FALLBACK_SOURCE_NAME


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
                        f"is included in .gitignore."
                    )
            elif key_name in [
                KEY_ENABLE_HTTP2,
                KEY_VERIFY_SSL,
                KEY_TIMEOUT,
                KEY_DEVELOPMENT_MODE,
            ]:
                self._modify_history(key_name, value)


def reinitiate_config(
    ignore_essential_validation: bool = False, ignore_already_validated: bool = False
) -> None:
    from ..core_validators import Validate, ValidationError, Exit
    from .validators import MainConfigurationValidator

    limited_to: Optional[list] = []
    if not ignore_essential_validation:
        if not ignore_already_validated:
            for validator in MainConfigurationValidator.ALL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = None
        try:
            validated_fields = Validate(
                MainConfigurationValidator(limited_to=limited_to)
            ).get()
        except ValidationError:
            raise Exit(1)
        else:
            for validator in limited_to:
                validator.ALREADY_VALIDATED = True
            apply_settings = ApplyConfigHistory(validated_fields)
            apply_settings.apply()
    else:
        if not ignore_already_validated:
            for validator in MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS
        try:
            validated_fields = Validate(
                MainConfigurationValidator(limited_to=limited_to)
            ).get()
        except ValidationError:
            raise Exit(1)
        else:
            for validator in limited_to:
                validator.ALREADY_VALIDATED = True
            apply_settings = ApplyConfigHistory(validated_fields)
            apply_settings.apply()
