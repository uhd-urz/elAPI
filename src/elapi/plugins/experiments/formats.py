from typing import Union

from ...styles import BaseFormat


class BinaryFormat:
    def __call__(self, data: bytes) -> bytes:
        if not isinstance(data, bytes):
            raise TypeError(
                f"data for '{self.__class__.__name__}' must be a bytes object."
            )
        return data


class PDFFormat(BaseFormat, BinaryFormat):
    name: str = "pdf"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^pdfa?$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class ZIPFormat(BaseFormat, BinaryFormat):
    name: str = "zip"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^zipa?$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class ELNFormat(BaseFormat, BinaryFormat):
    name: str = "eln"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^eln$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class CSVFormat(BaseFormat, BinaryFormat):
    name: str = "csv"
    convention: str = name

    @classmethod
    def pattern(cls) -> str:
        return r"^csv$"

    def __call__(self, data: Union[bytes, str]) -> Union[bytes, str]:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
            # CSV data as binary written to a file will just show text in binary format as well.
            # We'd like to save CSV as text CSV.
            # Conversion to other encoding format can be done later with Export class.
        return data


class QRPNGFormat(BaseFormat, BinaryFormat):
    name: str = "qrpng"
    convention: list[str] = ["png", "qrpng"]

    @classmethod
    def pattern(cls) -> str:
        return r"^qrpng$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)
