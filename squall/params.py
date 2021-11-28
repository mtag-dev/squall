from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Union

Number = Union[int, float, Decimal]


class ValidatorTypes(Enum):
    numeric = "numeric"
    string = "string"


@dataclass
class Num:
    in_ = ValidatorTypes.numeric
    gt: Optional[Number] = None
    ge: Optional[Number] = None
    lt: Optional[Number] = None
    le: Optional[Number] = None


@dataclass
class Str:
    in_ = ValidatorTypes.string
    min_len: Optional[int] = None
    max_len: Optional[int] = None


class ParamTypes(Enum):
    param = "path_params"
    query = "query_params"
    header = "headers"
    path = "path_params"
    cookie = "cookies"


class ParamOpenAPI(Enum):
    param = "path"
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


@dataclass
class CommonParam:
    # in_: ParamTypes
    default: Any = Ellipsis
    origin: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    valid: Optional[Union[Str, Num]] = None
    example: Optional[Any] = None
    examples: Optional[Dict[str, Any]] = None
    deprecated: Optional[bool] = None


@dataclass
class Path(CommonParam):
    in_ = ParamTypes.path
    openapi_ = ParamOpenAPI.path


@dataclass
class Param(CommonParam):
    in_ = ParamTypes.path
    openapi_ = ParamOpenAPI.path


@dataclass
class Query(CommonParam):
    in_ = ParamTypes.query
    openapi_ = ParamOpenAPI.query


@dataclass
class Header(CommonParam):
    in_ = ParamTypes.header
    openapi_ = ParamOpenAPI.header


@dataclass
class Cookie(CommonParam):
    in_ = ParamTypes.cookie
    openapi_ = ParamOpenAPI.cookie


@dataclass
class Body:
    default: Any = Ellipsis
    media_type: str = "application/json"
    embed: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Dict[str, Any]] = None


@dataclass
class Form(Body):
    media_type: str = "application/x-www-form-urlencoded"
    origin: Optional[str] = None


@dataclass
class File(Body):
    media_type: str = "multipart/form-data"
    origin: Optional[str] = None
