import inspect
import typing
from dataclasses import is_dataclass
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel
from pydantic.fields import FieldInfo, Undefined
from squall.params import Body, CommonParam, File, Form, Num, Str
from squall.requests import Request


class ParameterSourceType(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


# class ParameterVariableType(Enum):
#     int = "integer"
#     Decimal = "number"
#     float = "number"
#     bool = "boolean"
#     str = "string"
#     bytes = "string"


type_mapping: Dict[str, str] = {
    "int": "integer",
    "Decimal": "number",
    "float": "number",
    "bool": "boolean",
    "str": "string",
    "bytes": "string",
}


class HeadParam:
    def __init__(self, name: str, value: inspect.Parameter, source: str) -> None:
        self._annotation = value.annotation
        self._default = value.default
        self._empty = value.empty

        self.name = name
        self.source = source
        self.is_array, self.convertor = self.get_convertor()
        self.validate, self.statements = self.get_validation_statements()

    @property
    def origin(self) -> str:
        return getattr(self._default, "origin", None) or self.name

    @property
    def default(self) -> Any:
        default = Ellipsis
        if isinstance(self._default, CommonParam):
            default = self._default.default
        elif type(self._default) in (int, float, Decimal, str, bytes, type(None)):
            default = self._default
        return default

    def get_validation_statements(self) -> Tuple[Optional[str], Dict[str, Any]]:
        validate, statements = None, {}
        if hasattr(self._default, "valid") and isinstance(
            self._default.valid, (Num, Str)
        ):
            validate = self._default.valid.in_.value
            for constraint in self._default.valid.get_constraints():
                value = getattr(self._default.valid, constraint)
                if value is not None:
                    statements[constraint] = value
        return validate, statements

    def get_convertor(self) -> Tuple[bool, str]:
        is_array, convertor = False, "str"
        args, origin = get_args(self._annotation), get_origin(self._annotation)
        if origin is Union:
            if type(None) in args:
                if get_origin(args[0]) == list:
                    is_array, _convertor = True, get_args(args[0])[0]
                else:
                    is_array, _convertor = False, args[0]
                convertor = getattr(_convertor, "__name__", None)
        elif origin == list:
            try:
                is_array, convertor = True, args[0].__name__
            except Exception:
                """List[Any] should be implemented"""
        elif (
            hasattr(self._annotation, "__name__")
            and self._annotation.__name__ != "_empty"
        ):
            convertor = self._annotation.__name__
        return is_array, convertor

    @property
    def spec(self) -> Dict[str, Any]:
        source_mapping = {
            "path_params": "path",
            "query_params": "query",
            "headers": "header",
            "cookies": "cookie",
        }

        item: Dict[str, Any] = {}
        item["type"] = type_mapping.get(self.convertor, "string")

        schema: Dict[str, Any]
        if self.is_array:
            schema = {"type": "array", "items": item}
        else:
            schema = item
            if self.statements.get("ge") is not None:
                schema["minimum"] = self.statements["ge"]
                schema["exclusiveMinimum"] = False
            elif self.statements.get("gt") is not None:
                schema["minimum"] = self.statements["gt"]
                schema["exclusiveMinimum"] = True

            if self.statements.get("le") is not None:
                schema["maximum"] = self.statements["le"]
                schema["exclusiveMaximum"] = False
            elif self.statements.get("lt") is not None:
                schema["maximum"] = self.statements["lt"]
                schema["exclusiveMaximum"] = True

        result = {
            "required": self.default == Ellipsis,
            "schema": schema,
            "name": self.origin or self.name,
            "in": source_mapping[self.source],
        }

        description = getattr(self._default, "description", None)
        if description is not None:
            result["description"] = description

        example = getattr(self._default, "example", None)
        if example != Undefined and example:
            result["example"] = example

        examples = getattr(self._default, "examples", None)
        if examples:
            result["examples"] = examples

        deprecated = getattr(self._default, "deprecated", None)
        if deprecated:
            result["deprecated"] = True

        return result


def get_handler_head_params(func: Callable[..., Any]) -> List[HeadParam]:
    signature = inspect.signature(func)
    results = []
    for k, v in signature.parameters.items():
        source = None
        if isinstance(v.default, CommonParam):
            source = v.default.in_.value
        elif v.default is v.empty:
            res = get_annotation_affiliation(v.annotation)
            if res is None:
                source = "path_params"
        elif type(v.default) in (int, float, Decimal, str, bytes, type(None)):
            source = "path_params"

        if source is not None:
            results.append(HeadParam(name=k, value=v, source=source))

    return results


def get_annotation_affiliation(annotation: Any) -> typing.Optional[Any]:
    """Helper for classifying affiliation of parameter

    :param annotation: annotation record
    :returns: classified value or None
    """
    if annotation == Request:
        return "request"
    elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return "model"
    elif inspect.isclass(annotation) and is_dataclass(annotation):
        return "model"
    elif isinstance(annotation, FieldInfo):
        return "model"
    # elif isinstance(v.default, (Form, File)):
    #     return "form"
    return None


def get_handler_body_params(func: Callable[..., Any]) -> List[Dict[str, Any]]:
    """Reads meta information from callable inspection.
    Filter out only parameters that appear from BODY.
    Provides all necessary data for build validation.

    :param func: callable for inspection
    """
    signature = inspect.signature(func)
    results = []
    for k, v in signature.parameters.items():
        param: Dict[str, Any] = {"name": k}
        annotation = v.annotation
        if annotation == Request:
            param["kind"] = "request"
        elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            param["kind"] = "model"
            param["model_class"] = annotation
        elif inspect.isclass(annotation) and is_dataclass(annotation):
            param["kind"] = "model"
            param["model_class"] = annotation
        elif isinstance(annotation, FieldInfo):
            param["kind"] = "field"
            param["model_class"] = annotation
        elif isinstance(v.default, (Form, File)):
            param["kind"] = "form"
            param["model_class"] = annotation
            # param['origin'] = v.default
        elif isinstance(v.default, Body):
            param["kind"] = "body"
        else:
            continue

        results.append(param)

    return results


class MyModel(BaseModel):
    a: int


if __name__ == "__main__":

    def func(req: Request, a: MyModel) -> None:
        pass

    from pprint import pprint

    pprint(get_handler_body_params(func))
