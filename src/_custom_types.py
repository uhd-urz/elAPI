class ListWithID(list):
    def __init__(self, iterable):
        super().__init__(item for item in iterable)
