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
        cls._names.append(cls.name)
        cls._conventions.append(cls.convention)

    @property
    @abstractmethod
    def name(self):
        ...

    @property
    @abstractmethod
    def convention(self) -> Union[str, Iterable[str, ...]]:
        return self.name

    @convention.setter
    def convention(self, value):
        ...

    @classmethod
    def supported_formatters(cls) -> dict[str:"BaseFormat", ...]:
        return cls._registry

    @classmethod
    def supported_formatter_names(cls) -> list[str, ...]:
        return cls._names

    @classmethod
    @abstractmethod
    def pattern(cls):
        ...

    @abstractmethod
    def __call__(self, data: Any):
        ...


class JSONFormat(BaseFormat):
    name: str = "json"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^json$"

    def __call__(self, data: Any) -> str:
        import json

        return json.dumps(data, indent=2, ensure_ascii=True)


class YAMLFormat(BaseFormat):
    name: str = "yaml"
    convention: list[str, ...] = ["yml", "yaml"]

    @classmethod
    def pattern(cls) -> str:
        return r"^ya?ml$"

    def __call__(self, data: Any) -> str:
        import yaml

        return yaml.dump(data, indent=2, allow_unicode=True)


class TXTFormat(BaseFormat):
    name: str = "txt"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^(plain)?te?xt$"

    def __call__(self, data: Any) -> str:
        from pprint import pformat

        return pformat(data)


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
        raise ValueError(
            f"'{value}' isn't a supported language format! "
            f"Supported formats are: {BaseFormat.supported_formatter_names()}."
        )


class Format:
    def __new__(cls, language: str, /) -> BaseFormat:
        validator = ValidateLanguage(language)
        return validator.formatter()


BaseFormat.register(Format)
