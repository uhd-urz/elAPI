from pathlib import Path
from typing import Optional, Iterable

from ._config_history import MinimalActiveConfiguration, FieldValueWithKey
from ..core_validators import Validator, CriticalValidationError
from ..styles import stdin_console, Missing
from ..styles.highlight import NoteText


class HostConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, minimal_active_config_obj: MinimalActiveConfiguration, /):
        self.active_configuration = minimal_active_config_obj

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

    def validate(self) -> str:
        from ..loggers import Logger
        from .config import KEY_HOST

        logger = Logger()
        _HOST_EXAMPLE: str = f"{KEY_HOST.lower()}: 'https://demo.elabftw.net/api/v2'"

        if isinstance(self.active_configuration.get_value(KEY_HOST), Missing):
            logger.critical(f"'{KEY_HOST.lower()}' is missing from configuration file.")
            stdin_console.print(
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
            stdin_console.print(
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
            stdin_console.print(
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
            stdin_console.print(
                NoteText(
                    f"Host contains the URL of the root API endpoint. Example:"
                    f"\n{_HOST_EXAMPLE}",
                )
            )
            raise CriticalValidationError
        return host


class APITokenConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, minimal_active_config_obj: MinimalActiveConfiguration, /):
        self.active_configuration = minimal_active_config_obj

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

    def validate(self) -> str:
        from ..loggers import Logger
        from .config import KEY_API_TOKEN

        logger = Logger()
        if isinstance(self.active_configuration.get_value(KEY_API_TOKEN), Missing):
            logger.critical(
                f"'{KEY_API_TOKEN.lower()}' is missing from configuration file."
            )
            stdin_console.print(
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
            stdin_console.print(
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
            stdin_console.print(
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
            stdin_console.print(
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
            stdin_console.print(
                NoteText(
                    "An API token with at least read-access is required to make requests.",
                )
            )
            raise CriticalValidationError
        return api_token


class ExportDirConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, minimal_active_config_obj: MinimalActiveConfiguration, /):
        self.active_configuration = minimal_active_config_obj

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

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
                    stdin_console.print(
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


class BooleanWithFallbackConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(
        self,
        minimal_active_config_obj: MinimalActiveConfiguration,
        /,
        key_name: str,
        fallback_value: bool,
    ):
        self.active_configuration = minimal_active_config_obj
        self.key_name = key_name
        self.fallback_value = fallback_value

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

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


class DecimalWithFallbackConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(
        self,
        minimal_active_config_obj: MinimalActiveConfiguration,
        /,
        key_name: str,
        fallback_value: float,
    ):
        self.active_configuration = minimal_active_config_obj
        self.key_name = key_name
        self.fallback_value = fallback_value

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

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


class MainConfigurationValidator(Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(
        self,
        *,
        limited_to: Optional[Iterable[type[Validator]]] = None,
    ):
        from ._config_history import MinimalActiveConfiguration

        self.active_configuration = MinimalActiveConfiguration()
        self.limited_to = limited_to

    @property
    def limited_to(self) -> list[type[Validator]]:
        return self._limited_to

    @limited_to.setter
    def limited_to(self, value):
        if value is None:
            self._limited_to = [
                HostConfigurationValidator,
                APITokenConfigurationValidator,
                ExportDirConfigurationValidator,
                BooleanWithFallbackConfigurationValidator,
                DecimalWithFallbackConfigurationValidator,
            ]
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

    @property
    def active_configuration(self) -> MinimalActiveConfiguration:
        return self._active_configuration

    @active_configuration.setter
    def active_configuration(self, value: MinimalActiveConfiguration):
        if not isinstance(value, MinimalActiveConfiguration):
            raise TypeError(
                f"Value must be an instance of {MinimalActiveConfiguration.__name__}."
            )
        self._active_configuration = value

    def validate(self) -> list[FieldValueWithKey]:
        from ..core_validators import Validate, ValidationError
        from .config import KEY_EXPORT_DIR
        from .config import KEY_ENABLE_HTTP2, ENABLE_HTTP2_DEFAULT_VAL
        from .config import KEY_VERIFY_SSL, VERIFY_SSL_DEFAULT_VAL
        from .config import KEY_UNSAFE_TOKEN_WARNING, UNSAFE_TOKEN_WARNING_DEFAULT_VAL
        from .config import KEY_TIMEOUT, TIMEOUT_DEFAULT_VAL
        from .config import KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE_DEFAULT_VAL

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
                    KEY_UNSAFE_TOKEN_WARNING,
                    UNSAFE_TOKEN_WARNING_DEFAULT_VAL,
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
                        key_name,
                        default_value,
                    )
                ).get()
                # Update validated_fields after validation
                validated_fields.append(FieldValueWithKey(key_name, value))
        if DecimalWithFallbackConfigurationValidator in self.limited_to:
            timeout = Validate(
                DecimalWithFallbackConfigurationValidator(
                    self.active_configuration,
                    KEY_TIMEOUT,
                    TIMEOUT_DEFAULT_VAL,
                )
            ).get()
            # Update validated_fields after validation
            validated_fields.append(FieldValueWithKey(KEY_TIMEOUT, timeout))
        return validated_fields
