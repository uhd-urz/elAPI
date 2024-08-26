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
    package_identifier: str = __package__

    @classmethod
    def pattern(cls) -> str:
        return r"^pdf$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class PDFAFormat(PDFFormat, BaseFormat):
    name: str = "pdfa"
    convention: str = PDFFormat.convention
    reference: str = f"{name.upper()} (a.k.a PDF/A)"

    @classmethod
    def pattern(cls) -> str:
        return r"^pdfa$"


class ZIPFormat(BaseFormat, BinaryFormat):
    name: str = "zip"
    convention: str = name
    package_identifier: str = __package__

    @classmethod
    def pattern(cls) -> str:
        return r"^zip$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class ZIPAFormat(ZIPFormat, BinaryFormat):
    name: str = "zipa"
    convention: str = ZIPFormat.convention
    reference: str = f"{name.upper()} (mainly PDFA inside a ZIP)"

    @classmethod
    def pattern(cls) -> str:
        return r"^zipa$"


class ELNFormat(BaseFormat, BinaryFormat):
    name: str = "eln"
    convention: str = name
    package_identifier: str = __package__

    @classmethod
    def pattern(cls) -> str:
        return r"^eln$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)


class CSVFormat(BaseFormat, BinaryFormat):
    name: str = "csv"
    convention: str = name
    package_identifier: str = __package__

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
    package_identifier: str = __package__

    @classmethod
    def pattern(cls) -> str:
        return r"^qrpng$"

    def __call__(self, data: bytes) -> bytes:
        return BinaryFormat().__call__(data)
