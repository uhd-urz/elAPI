import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Optional, Self, Union

from .. import APP_NAME
from .base import __PACKAGE_IDENTIFIER__ as styles_package_identifier


class BaseFormat(ABC):
    _registry: dict[str, dict[str, type[Self]]] = {styles_package_identifier: {}}
    _names: dict[str, list[str]] = {styles_package_identifier: []}
    _conventions: dict[str, list[str]] = {styles_package_identifier: []}

    # noinspection PyTypeChecker
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.package_identifier not in cls._registry:
            cls._registry[cls.package_identifier] = {}
            cls._registry[cls.package_identifier].update(
                cls._registry[styles_package_identifier]
            )
        if cls.package_identifier not in cls._names:
            cls._names[cls.package_identifier] = []
            cls._names[cls.package_identifier] += cls._names[styles_package_identifier]
        if cls.package_identifier not in cls._conventions:
            cls._conventions[cls.package_identifier] = []
            cls._conventions[cls.package_identifier] += cls._conventions[
                styles_package_identifier
            ]
        if cls.name is None:
            if cls.package_identifier == styles_package_identifier:
                raise ValueError(
                    f"Attribute 'name' cannot be None for when package_identifier "
                    f"is {styles_package_identifier} as it will "
                    f"remove {APP_NAME} built-in formats."
                )
            existing_cls = cls._registry[cls.package_identifier].pop(cls.pattern())
            try:
                cls._names[cls.package_identifier].remove(existing_cls.name)
                cls._conventions[cls.package_identifier].remove(existing_cls.convention)
            except ValueError as e:
                raise KeyError(
                    f"Attribute 'name' is None, which will remove "
                    f"{cls!r} as a formatter, "
                    f"but class {cls!r} was never registered before!"
                ) from e
        else:
            cls._registry[cls.package_identifier][cls.pattern()] = cls
            if cls.name not in cls._names[cls.package_identifier]:
                cls._names[cls.package_identifier].append(cls.name)
            if cls.convention not in cls._conventions[cls.package_identifier]:
                cls._conventions[cls.package_identifier].append(cls.convention)

    @property
    @abstractmethod
    def name(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def convention(self) -> Union[str, Iterable[str], None]:
        return self.name

    @convention.setter
    def convention(self, value): ...

    @property
    @abstractmethod
    def package_identifier(self) -> Optional[str]: ...

    @classmethod
    def supported_formatters(
        cls, package_identifier: Optional[str] = None
    ) -> dict[str, dict[str, type[Self]]] | dict[str, type[Self]]:
        if package_identifier is None:
            return cls._registry
        return cls._registry[package_identifier]

    @classmethod
    def supported_formatter_names(
        cls, package_identifier: Optional[str] = None
    ) -> dict[str, list[str]] | list[str]:
        if package_identifier is None:
            return cls._names
        return cls._names[package_identifier]

    @classmethod
    @abstractmethod
    def pattern(cls): ...

    @abstractmethod
    def __call__(self, data: Any): ...


class FormatError(Exception): ...


class JSONFormat(BaseFormat):
    name: str = "json"
    convention: str = name
    package_identifier: str = styles_package_identifier

    @classmethod
    def pattern(cls) -> str:
        return r"^json$"

    def __call__(self, data: Any) -> str:
        import json

        return json.dumps(
            data, indent=2, ensure_ascii=False
        )  # ensure_ascii==False allows unicode


class YAMLFormat(BaseFormat):
    name: str = "yaml"
    convention: list[str] = ["yml", "yaml"]
    package_identifier: str = styles_package_identifier

    @classmethod
    def pattern(cls) -> str:
        return r"^ya?ml$"

    def __call__(self, data: Any) -> str:
        import yaml

        return yaml.dump(data, indent=2, allow_unicode=True, sort_keys=False)


class CSVFormat(BaseFormat):
    name: str = "csv"
    convention: str = name
    package_identifier: str = styles_package_identifier

    @classmethod
    def pattern(cls) -> str:
        return r"^csv$"

    def __call__(self, data: Any) -> str:
        from csv import DictWriter
        from io import StringIO

        with StringIO() as csv_buffer:
            writer: DictWriter = DictWriter(csv_buffer, fieldnames=[])
            if isinstance(data, dict):
                writer.fieldnames = data.keys()
                writer.writeheader()
                writer.writerow(data)
                csv_as_string = csv_buffer.getvalue()
            elif isinstance(data, Iterable):
                for item in data:
                    if not isinstance(item, dict):
                        raise FormatError(
                            "Only dictionaries or iterables of dictionaries can be formatted to CSV."
                        )
                    if not writer.fieldnames:
                        writer.fieldnames = item.keys()
                        writer.writeheader()
                    if len(item.items()) > len(writer.fieldnames):
                        raise FormatError(
                            "Iterable of dictionary contains insistent length of key items."
                        )
                    writer.writerow(item)
                csv_as_string = csv_buffer.getvalue()
        return csv_as_string


class TXTFormat(BaseFormat):
    name: str = "txt"
    convention: list[str] = ["txt"]
    package_identifier: str = styles_package_identifier

    @classmethod
    def pattern(cls) -> str:
        return r"^txt|text|plaintext$"

    def __call__(self, data: Any) -> str:
        return str(data)


class RegisterFormattingLanguage:
    def __init__(self, language: str, *, package_identifier: str):
        self.package_identifier = package_identifier
        self._register = language

    @property
    def package_identifier(self) -> str:
        return self._package_identifier

    @package_identifier.setter
    def package_identifier(self, value):
        if not isinstance(value, str):
            raise ValueError(f"{value} must be an instance of str.")
        self._package_identifier = value

    @property
    def _register(self):
        raise AttributeError(
            "'_register' isn't meant to be called directly! "
            "Use attributes 'name' and 'formatter'."
        )

    @_register.setter
    def _register(self, value):
        try:
            supported_formatters = BaseFormat.supported_formatters()[
                self.package_identifier
            ]
        except KeyError as e:
            raise KeyError(
                f"Package identifier '{self.package_identifier}' not found "
                f"in registered supported_formatters dictionary!"
            ) from e
        for pattern, formatter in supported_formatters.items():
            if re.match(rf"{pattern}", value, flags=re.IGNORECASE):
                self.name: str = formatter.name
                self.convention: Union[str, Iterable[str]] = formatter.convention
                self.formatter: type[BaseFormat] = formatter
                return
        raise FormatError(
            f"'{value}' isn't a supported language format! "
            f"Supported formats are: "
            f"{BaseFormat.supported_formatter_names(self.package_identifier)}."
        )


class Format:
    def __new__(cls, language: str, /, *, package_identifier: str) -> BaseFormat:
        lang = RegisterFormattingLanguage(
            language, package_identifier=package_identifier
        )
        return lang.formatter()


BaseFormat.register(Format)
