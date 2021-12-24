import typing
from decimal import Decimal
from uuid import UUID


class Convertor:
    __slots__ = ["alias", "regex", "type"]

    alias: str
    regex: str
    type: typing.Any

    def convert(self, value: str) -> typing.Any:
        raise NotImplementedError()


class StrConvertor(Convertor):
    alias: str = "str"
    regex: str = r"^.*$"
    type = str

    @staticmethod
    def convert(value: str) -> typing.Any:
        return value


class IntConvertor(Convertor):
    alias: str = "int"
    regex: str = r"^[0-9]+$"
    type = int

    @staticmethod
    def convert(value: str) -> int:
        return int(value)


class FloatConvertor(Convertor):
    alias: str = "float"
    regex: str = r"^[0-9]+(.[0-9]+)?$"
    type = float

    @staticmethod
    def convert(value: str) -> float:
        return float(value)


class DecimalConvertor(Convertor):
    alias: str = "decimal"
    regex: str = r"^[0-9]+(.[0-9]+)?$"
    type = Decimal

    @staticmethod
    def convert(value: str) -> Decimal:
        return Decimal(value)


class UUIDConvertor(Convertor):
    alias: str = "uuid"
    regex: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    type = UUID

    @staticmethod
    def convert(value: str) -> UUID:
        return UUID(value)


class ConvertorsDatabase:
    __slots__ = ["convertors"]

    def __init__(self) -> None:
        self.convertors: typing.Dict[str, Convertor] = {}

    def add_convertor(self, convertor: typing.Type[Convertor]) -> None:
        self.convertors[convertor.alias] = convertor()


CONVERTORS = [
    StrConvertor,
    IntConvertor,
    FloatConvertor,
    DecimalConvertor,
    UUIDConvertor,
]

database = ConvertorsDatabase()
for convertor in CONVERTORS:
    database.add_convertor(convertor)
