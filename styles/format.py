import re
from abc import abstractmethod, ABC
from typing import Any


class BaseFormat(ABC):
    _registry = {}
    _names = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.pattern()] = cls
        cls._names.append(cls.name)

    @property
    @abstractmethod
    def name(self):
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

    @classmethod
    def pattern(cls) -> str:
        return r"^json$"

    def __call__(self, data: Any) -> str:
        import json

        return json.dumps(data, indent=2, ensure_ascii=True)


class YAMLFormat(BaseFormat):
    name = "yaml"

    @classmethod
    def pattern(cls) -> str:
        return r"^ya?ml$"

    def __call__(self, data: Any) -> str:
        import yaml

        return yaml.dump(data, indent=2, allow_unicode=True)


class TXTFormat(BaseFormat):
    name = "txt"

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
