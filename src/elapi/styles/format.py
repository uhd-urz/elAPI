import re
from abc import abstractmethod, ABC
from collections.abc import Iterable
from typing import Any, Union


class BaseFormat(ABC):
    _registry: dict[str:Any, ...] = {}
    _names: list[str, ...] = []
    _conventions: list[str, ...] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.pattern()] = cls
        if cls.name not in cls._names:
            cls._names.append(cls.name)
        cls._conventions.append(cls.convention)

    @property
    @abstractmethod
    def name(self): ...

    @property
    @abstractmethod
    def convention(self) -> Union[str, Iterable[str, ...]]:
        return self.name

    @convention.setter
    def convention(self, value): ...

    @classmethod
    def supported_formatters(cls) -> dict[str:"BaseFormat", ...]:
        return cls._registry

    @classmethod
    def supported_formatter_names(cls) -> list[str, ...]:
        return cls._names

    @classmethod
    @abstractmethod
    def pattern(cls): ...

    @abstractmethod
    def __call__(self, data: Any): ...


class FormatError(Exception): ...


class JSONFormat(BaseFormat):
    name: str = "json"
    convention: str = name

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
    convention: list[str, ...] = ["yml", "yaml"]

    @classmethod
    def pattern(cls) -> str:
        return r"^ya?ml$"

    def __call__(self, data: Any) -> str:
        import yaml

        return yaml.dump(data, indent=2, allow_unicode=True, sort_keys=False)


class TXTFormat(BaseFormat):
    name: str = "txt"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^(plain)?te?xt$"

    def __call__(self, data: Any) -> str:
        from pprint import pformat

        return pformat(data)


class CSVFormat(BaseFormat):
    name: str = "csv"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^csv$"

    def __call__(self, data: Any) -> str:
        from csv import DictWriter
        from io import StringIO

        with StringIO() as csv_buffer:
            writer = DictWriter(csv_buffer, fieldnames=[])
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


class ValidateLanguage:
    def __init__(self, language: str):
        self._validated = language

    @property
    def _validated(self):
        raise AttributeError(
            "'_validated' isn't meant to be called directly! Use attributes 'name' and 'formatter'."
        )

    @_validated.setter
    def _validated(self, value):
        for pattern, formatter in BaseFormat.supported_formatters().items():
            if re.match(rf"{pattern}", value, flags=re.IGNORECASE):
                self.name: str = formatter.name
                self.convention: Union[str, Iterable[str, ...]] = formatter.convention
                self.formatter: type(BaseFormat) = formatter
                return
        raise FormatError(
            f"'{value}' isn't a supported language format! "
            f"Supported formats are: {BaseFormat.supported_formatter_names()}."
        )


class Format:
    def __new__(cls, language: str, /) -> BaseFormat:
        validator = ValidateLanguage(language)
        return validator.formatter()


BaseFormat.register(Format)
