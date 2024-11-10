from pathlib import Path
from typing import Optional, Iterable, Union

from ._config_history import MinimalActiveConfiguration, FieldValueWithKey
from ..core_validators import Validator, CriticalValidationError
from ..styles import stdout_console, Missing
from ..styles.highlight import NoteText


class ConfigurationValidation:
    def __init__(
        self, minimal_active_config_obj: Union[MinimalActiveConfiguration, dict], /
    ):
        self.active_configuration = minimal_active_config_obj

    @property
    def active_configuration(self) -> Union[MinimalActiveConfiguration, dict]:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, (MinimalActiveConfiguration, dict)):
            raise TypeError(
                f"Value must be an instance of "
                f"{MinimalActiveConfiguration.__name__} or {dict.__name__}."
            )
        self._active_configuration = value


class HostConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args):
        super().__init__(*args)

    def validate(self) -> str:
        from ..loggers import Logger
        from .config import KEY_HOST

        logger = Logger()
        _HOST_EXAMPLE: str = f"{KEY_HOST.lower()}: 'https://demo.elabftw.net/api/v2'"

        if isinstance(self.active_configuration.get_value(KEY_HOST), Missing):
            logger.critical(f"'{KEY_HOST.lower()}' is missing from configuration file.")
            stdout_console.print(
                NoteText(
                    f"Host is the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        if (host := self.active_configuration.get_value(KEY_HOST)) is None:
            logger.critical(
                f"'{KEY_HOST.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            stdout_console.print(
                NoteText(
                    f"Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        if not isinstance(host, str):
            logger.critical(
                f"'{KEY_HOST.lower()}' is detected in configuration file, "
                f"but it's not a string."
            )
            stdout_console.print(
                NoteText(
                    f"Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        if not host:
            logger.critical(
                f"'{KEY_HOST.lower()}' is detected in configuration file, "
                f"but it's empty."
            )
            stdout_console.print(
                NoteText(
                    f"Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        return host


class APITokenConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args):
        super().__init__(*args)

    def validate(self) -> str:
        from ..loggers import Logger
        from .config import KEY_API_TOKEN

        logger = Logger()
        if isinstance(self.active_configuration.get_value(KEY_API_TOKEN), Missing):
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is missing from configuration file."
            )
            stdout_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests."
                )
            )
            raise CriticalValidationError
        if (api_token := self.active_configuration.get_value(KEY_API_TOKEN)) is None:
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            stdout_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise CriticalValidationError
        try:
            api_token = api_token.token
        except AttributeError:
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is detected in configuration file, "
                f"but it's not a string."
            )
            stdout_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise CriticalValidationError
        if not isinstance(api_token, str):
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is detected in configuration file, "
                f"but it's not a string."
            )
            stdout_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise CriticalValidationError
        if not api_token:
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is detected in configuration file, "
                f"but it's empty."
            )
            stdout_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise CriticalValidationError
        return api_token


class ExportDirConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args):
        super().__init__(*args)

    def validate(self) -> Path:
        import errno
        from ..loggers import Logger
        from .config import KEY_EXPORT_DIR
        from ..core_validators import (
            Validate,
            PathValidator,
            ValidationError,
            PathValidationError,
        )

        logger = Logger()

        def get_validated_fallback():
            from .._names import APP_NAME
            from .config import _XDG_DOWNLOAD_DIR, FALLBACK_EXPORT_DIR
            from ..path import ProperPath

            ACTUAL_FALLBACK_EXPORT_DIR = FALLBACK_EXPORT_DIR
            if _XDG_DOWNLOAD_DIR is not None:
                try:
                    _XDG_DOWNLOAD_DIR = ProperPath(_XDG_DOWNLOAD_DIR)
                except ValueError:
                    _XDG_DOWNLOAD_DIR = None
                else:
                    if _XDG_DOWNLOAD_DIR.kind != "dir":
                        _XDG_DOWNLOAD_DIR = None
                if ProperPath(FALLBACK_EXPORT_DIR).kind != "dir":
                    FALLBACK_EXPORT_DIR = None
            try:
                fallback_export_dir = Validate(
                    PathValidator([_XDG_DOWNLOAD_DIR, FALLBACK_EXPORT_DIR])
                ).get()
            except ValidationError:
                logger.critical(
                    f"{APP_NAME} couldn't validate {ACTUAL_FALLBACK_EXPORT_DIR} to store exported data. "
                    f"This is a fatal error. To quickly fix this error define an export directory "
                    f"with '{KEY_EXPORT_DIR}' in configuration file. {APP_NAME} will not run!"
                )
                raise CriticalValidationError
            else:
                return fallback_export_dir

        if isinstance(
            config_export_dir := self.active_configuration.get_value(KEY_EXPORT_DIR),
            (Missing, type(None)),
        ):
            return get_validated_fallback()
        else:
            if not isinstance(config_export_dir, str):
                logger.warning(
                    f"'{KEY_EXPORT_DIR.lower()}' is detected in configuration file, "
                    f"but it's not a string."
                )
                return get_validated_fallback()
            if not config_export_dir:
                return get_validated_fallback()
            try:
                export_dir = Validate(PathValidator(config_export_dir)).get()
            except PathValidationError as e:
                if e.errno in [errno.EEXIST, errno.ENOTDIR]:
                    logger.warning(
                        f"{KEY_EXPORT_DIR}: {config_export_dir} from configuration file "
                        f"is not a directory!"
                    )
                    stdout_console.print(
                        NoteText(
                            "If you want to export to a file use '--export <path-to-file>'.\n",
                            stem="Note",
                        )
                    )
                logger.warning(
                    f"{KEY_EXPORT_DIR}: {config_export_dir} from configuration "
                    f"file couldn't be validated!"
                )
                return get_validated_fallback()
            else:
                return export_dir


class BooleanWithFallbackConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args, key_name: str, fallback_value: bool):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value

    def validate(self) -> bool:
        from ..loggers import Logger

        logger = Logger()
        if isinstance(
            value := self.active_configuration.get_value(self.key_name), Missing
        ):
            return self.fallback_value
        if value is None:
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            return self.fallback_value
        if not isinstance(value, bool):
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a boolean."
            )
            return self.fallback_value
        return value


class DecimalWithFallbackConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args, key_name: str, fallback_value: float):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value

    def validate(self) -> float:
        from ..loggers import Logger

        logger = Logger()
        if isinstance(
            value := self.active_configuration.get_value(self.key_name), Missing
        ):
            return self.fallback_value
        if value is None:
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            return self.fallback_value
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a float or integer."
            )
            return self.fallback_value
        return float(value)


class PluginConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args, key_name: str, fallback_value: dict):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value

    def validate(self) -> dict:
        from dynaconf.utils.boxing import DynaBox
        from ..loggers import Logger
        from ..configuration.config import CANON_YAML_EXTENSION, CONFIG_FILE_NAME
        from ..utils import add_message

        value: DynaBox = self.active_configuration.get_value(self.key_name)
        if isinstance(value, Missing):
            return self.fallback_value
        if value is None:
            message = (
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            add_message(message, Logger.CONSTANTS.WARNING, is_aggressive=True)
            return self.fallback_value
        if not isinstance(value, dict):
            message = (
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a {CANON_YAML_EXTENSION.upper()} dictionary."
            )
            add_message(message, Logger.CONSTANTS.WARNING, is_aggressive=True)
            return self.fallback_value
        else:
            value: dict = value.to_dict()  # Dynaconf uses Box:
            # https://github.com/cdgriffith/Box/wiki/Converters#dictionary
            for plugin_name, plugin_config in value.copy().items():
                if not isinstance(plugin_config, dict):
                    message = (
                        f"Configuration value for plugin '{plugin_name}' "
                        f"exists in '{CONFIG_FILE_NAME}' under '{self.key_name.lower()}', "
                        f"but it's not a {CANON_YAML_EXTENSION.upper()} dictionary. "
                        f"Plugin configuration for '{plugin_name}' will be ignored."
                    )
                    add_message(message, Logger.CONSTANTS.WARNING, is_aggressive=True)
                    value.pop(plugin_name)
        return value


class MainConfigurationValidator(ConfigurationValidation, Validator):
    ALL_VALIDATORS: list = [
        HostConfigurationValidator,
        APITokenConfigurationValidator,
        ExportDirConfigurationValidator,
        BooleanWithFallbackConfigurationValidator,
        DecimalWithFallbackConfigurationValidator,
        PluginConfigurationValidator,
    ]
    ESSENTIAL_VALIDATORS: list = [
        HostConfigurationValidator,
        APITokenConfigurationValidator,
    ]
    NON_ESSENTIAL_VALIDATORS: list = [
        ExportDirConfigurationValidator,
        BooleanWithFallbackConfigurationValidator,
        DecimalWithFallbackConfigurationValidator,
        PluginConfigurationValidator,
    ]
    __slots__ = ()

    def __init__(
        self,
        *,
        limited_to: Optional[Iterable[type[Validator]]] = None,
    ):
        from ._config_history import MinimalActiveConfiguration

        super().__init__(MinimalActiveConfiguration())
        self.limited_to = limited_to

    @property
    def limited_to(self) -> list[type[Validator]]:
        return self._limited_to

    @limited_to.setter
    def limited_to(self, value):
        if value is None:
            self._limited_to = MainConfigurationValidator.ALL_VALIDATORS
        else:
            if not isinstance(value, Iterable) and isinstance(value, str):
                raise ValueError(
                    f"Value must be an iterable of {Validator.__name__} subclass."
                )
            for _ in value:
                if not issubclass(_, Validator):
                    raise ValueError(
                        f"Value must be an iterable of {Validator.__name__} subclass."
                    )
            self._limited_to = value

    def validate(self) -> list[FieldValueWithKey]:
        from ..core_validators import Validate, ValidationError
        from .config import KEY_EXPORT_DIR
        from .config import KEY_ENABLE_HTTP2, ENABLE_HTTP2_DEFAULT_VAL
        from .config import KEY_VERIFY_SSL, VERIFY_SSL_DEFAULT_VAL
        from .config import KEY_UNSAFE_TOKEN_WARNING, UNSAFE_TOKEN_WARNING_DEFAULT_VAL
        from .config import KEY_TIMEOUT, TIMEOUT_DEFAULT_VAL
        from .config import KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE_DEFAULT_VAL
        from .config import KEY_PLUGIN_KEY_NAME, PLUGIN_DEFAULT_VALUE

        validated_fields: list[FieldValueWithKey] = []

        if HostConfigurationValidator in self.limited_to:
            _validate = Validate(HostConfigurationValidator(self.active_configuration))
            try:
                _validate()
            except ValidationError as e:
                raise e

        if APITokenConfigurationValidator in self.limited_to:
            _validate = Validate(
                APITokenConfigurationValidator(self.active_configuration)
            )
            try:
                _validate()
            except ValidationError as e:
                raise e

        if ExportDirConfigurationValidator in self.limited_to:
            try:
                export_dir = Validate(
                    ExportDirConfigurationValidator(self.active_configuration)
                ).get()
            except ValidationError as e:
                raise e
            # Update validated_fields after validation
            validated_fields.append(FieldValueWithKey(KEY_EXPORT_DIR, export_dir))
        if BooleanWithFallbackConfigurationValidator in self.limited_to:
            unsafe_token_warning = Validate(
                BooleanWithFallbackConfigurationValidator(
                    self.active_configuration,
                    key_name=KEY_UNSAFE_TOKEN_WARNING,
                    fallback_value=UNSAFE_TOKEN_WARNING_DEFAULT_VAL,
                )
            ).get()
            # Update validated_fields after validation
            validated_fields.append(
                FieldValueWithKey(KEY_UNSAFE_TOKEN_WARNING, unsafe_token_warning)
            )
            for key_name, default_value in [
                (KEY_ENABLE_HTTP2, ENABLE_HTTP2_DEFAULT_VAL),
                (KEY_VERIFY_SSL, VERIFY_SSL_DEFAULT_VAL),
                (KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE_DEFAULT_VAL),
            ]:
                value = Validate(
                    BooleanWithFallbackConfigurationValidator(
                        self.active_configuration,
                        key_name=key_name,
                        fallback_value=default_value,
                    )
                ).get()
                # Update validated_fields after validation
                validated_fields.append(FieldValueWithKey(key_name, value))
        if DecimalWithFallbackConfigurationValidator in self.limited_to:
            timeout = Validate(
                DecimalWithFallbackConfigurationValidator(
                    self.active_configuration,
                    key_name=KEY_TIMEOUT,
                    fallback_value=TIMEOUT_DEFAULT_VAL,
                )
            ).get()
            # Update validated_fields after validation
            validated_fields.append(FieldValueWithKey(KEY_TIMEOUT, timeout))
        if PluginConfigurationValidator in self.limited_to:
            plugin = Validate(
                PluginConfigurationValidator(
                    self.active_configuration,
                    key_name=KEY_PLUGIN_KEY_NAME,
                    fallback_value=PLUGIN_DEFAULT_VALUE,
                )
            ).get()
            # Update validated_fields after validation
            validated_fields.append(FieldValueWithKey(KEY_PLUGIN_KEY_NAME, plugin))
        return validated_fields
