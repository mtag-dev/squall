from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic.fields import FieldInfo, Undefined

Number = Union[int, float, Decimal]


class ValidatorTypes(Enum):
    numeric = "numeric"
    string = "string"


class Num(FieldInfo):
    in_ = ValidatorTypes.numeric

    def __init__(
        self,
        gt: Optional[Number] = None,
        ge: Optional[Number] = None,
        lt: Optional[Number] = None,
        le: Optional[Number] = None,
    ):
        self.in_ = self.in_
        super().__init__(gt=gt, ge=ge, lt=lt, le=le)


class Str(FieldInfo):
    in_ = ValidatorTypes.string

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        # starts: Optional[AnyStr] = None,
        # ends: Optional[AnyStr] = None,
    ):
        self.in_ = self.in_
        super().__init__(min_length=min_length, max_length=max_length)


class ParamTypes(Enum):
    param = "path_params"
    query = "query_params"
    header = "headers"
    path = "path_params"
    cookie = "cookies"


class CommonParam(FieldInfo):
    in_: ParamTypes

    def __init__(
        self,
        default: Any,
        *,
        origin: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        valid: Optional[Union[Str, Num]] = None,
        example: Any = Undefined,
        examples: Optional[Dict[str, Any]] = None,
        deprecated: Optional[bool] = None,
        **extra: Any,
    ):
        self.deprecated = deprecated
        self.example = example
        self.examples = examples
        self.origin = origin
        self.valid = valid
        super().__init__(
            default,
            title=title,
            description=description,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(CommonParam):
    in_ = ParamTypes.path


class Param(CommonParam):
    in_ = ParamTypes.param


class Query(CommonParam):
    in_ = ParamTypes.query


class Header(CommonParam):
    in_ = ParamTypes.header


class Cookie(CommonParam):
    in_ = ParamTypes.cookie


class Body(FieldInfo):
    def __init__(
        self,
        default: Any,
        *,
        embed: bool = False,
        media_type: str = "application/json",
        origin: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        example: Any = Undefined,
        examples: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ):
        self.embed = embed
        self.media_type = media_type
        self.example = example
        self.examples = examples
        super().__init__(
            default,
            origin=origin,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Form(Body):
    def __init__(
        self,
        default: Any,
        *,
        media_type: str = "application/x-www-form-urlencoded",
        origin: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        example: Any = Undefined,
        examples: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ):
        super().__init__(
            default,
            embed=True,
            media_type=media_type,
            origin=origin,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            example=example,
            examples=examples,
            **extra,
        )


class File(Form):
    def __init__(
        self,
        default: Any,
        *,
        media_type: str = "multipart/form-data",
        origin: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        example: Any = Undefined,
        examples: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ):
        super().__init__(
            default,
            media_type=media_type,
            origin=origin,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            example=example,
            examples=examples,
            **extra,
        )


#
# class Depends:
#     def __init__(
#         self, dependency: Optional[Callable[..., Any]] = None, *, use_cache: bool = True
#     ):
#         self.dependency = dependency
#         self.use_cache = use_cache
#
#     def __repr__(self) -> str:
#         attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
#         cache = "" if self.use_cache else ", use_cache=False"
#         return f"{self.__class__.__name__}({attr}{cache})"
#
#
# class Security(Depends):
#     def __init__(
#         self,
#         dependency: Optional[Callable[..., Any]] = None,
#         *,
#         scopes: Optional[Sequence[str]] = None,
#         use_cache: bool = True,
#     ):
#         super().__init__(dependency=dependency, use_cache=use_cache)
#         self.scopes = scopes or []
