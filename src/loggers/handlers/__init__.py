from abc import ABC, abstractmethod


class Handler(ABC):
    @abstractmethod
    def __eq__(self, other):
        if not (isinstance(other, Handler) and hasattr(other, "unique")):
            raise AssertionError(
                f"'{other}' must be an instance of {Handler.__class__} and "
                f"must implement the attribute 'unique'."
            )
        return self.unique == other.unique

    @abstractmethod
    def formatter(self):
        ...

    @abstractmethod
    def handler(self):
        ...

    @abstractmethod
    def unique(self):
        ...
