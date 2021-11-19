import inspect
import typing
from dataclasses import is_dataclass
from decimal import Decimal
from typing import Any, Callable, Dict, List, Union, get_args, get_origin

from pydantic import BaseModel
from squall.params import Body, CommonParam, File, Form, Num, Str
from squall.requests import Request
from pydantic.fields import FieldInfo


def get_handler_head_params(func: Callable[..., Any]) -> List[Dict[str, Any]]:
    """Reads meta information from callable inspection.
    Filter out only parameters that appear from HEAD.
    Provides all necessary data for build validation.

    :param func: callable for inspection
    """
    signature = inspect.signature(func)
    results = []
    for k, v in signature.parameters.items():
        param: Dict[str, Any] = {"name": k}
        args, origin = get_args(v.annotation), get_origin(v.annotation)
        if origin is Union:
            if type(None) in args:
                if get_origin(args[0]) == list:
                    param["as_list"] = True
                    convertor = get_args(args[0])[0]
                else:
                    convertor = args[0]

                param["convert"] = getattr(convertor, "__name__", None)

        elif origin == list:
            try:
                param["convert"] = args[0].__name__
            except Exception:
                """List[Any] should be implemented"""
            else:
                param["as_list"] = True

        elif hasattr(v.annotation, "__name__") and v.annotation.__name__ != "_empty":
            param["convert"] = v.annotation.__name__

        if param.get("convert") in ("int", "float", "Decimal"):
            param["validate"] = "numeric"
        elif param.get("convert") in ("str", "bytes"):
            param["validate"] = "string"

        if isinstance(v.default, CommonParam):
            param["source"] = v.default.in_.value
            if v.default.default != Ellipsis:
                param["default"] = v.default.default
        elif v.default is v.empty:
            res = get_annotation_affiliation(v.annotation)
            if res is None:
                param["source"] = "path_params"
        elif type(v.default) in (int, float, Decimal, str, bytes, type(None)):
            param["source"] = "path_params"
            param["default"] = v.default

        if hasattr(v.default, "valid") and isinstance(v.default.valid, (Num, Str)):
            param["validate"] = v.default.valid.in_.value
            for constraint in v.default.valid.get_constraints():
                value = getattr(v.default.valid, constraint)
                if value is not None:
                    param[constraint] = value

        if getattr(v.default, "origin", None) is not None:
            param["origin"] = v.default.origin

        if param.get("source") is not None:
            results.append(param)

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
