class Missing:
    """
    Missing is a string representation of a None object.
    """

    __slots__ = "_message"

    def __init__(self, message: str = "MISSING!"):
        self.message = message

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        if hasattr(value, "__str__"):
            self._message = str(value)

    def __str__(self) -> str:
        return self.message

    def __repr__(self):
        message = self.message
        return f"{self.__class__.__name__}({message=})"

    def __eq__(self, other) -> bool:
        if not other or isinstance(other, Missing):
            return True
        return False

    def __bool__(self) -> bool:
        return False
