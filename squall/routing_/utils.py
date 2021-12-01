import inspect
import typing
from dataclasses import asdict, is_dataclass
from decimal import Decimal
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

from squall.bindings import RequestField
from squall.params import (
    Body,
    CommonParam,
    Cookie,
    File,
    Form,
    Header,
    Num,
    Path,
    Query,
    Str,
)
from squall.requests import Request
from squall.utils import get_types
from starlette.websockets import WebSocket


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
    def alias(self) -> str:
        return getattr(self._default, "alias", None) or self.name

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
            statements = asdict(self._default.valid)
            validate = self._default.valid.in_.value
        return validate, statements

    def get_convertor(self) -> Tuple[bool, str]:
        is_array, convertor = False, "str"
        args, alias = get_args(self._annotation), get_origin(self._annotation)
        if alias is Union:
            if type(None) in args:
                if get_origin(args[0]) == list:
                    is_array, _convertor = True, get_args(args[0])[0]
                else:
                    is_array, _convertor = False, args[0]
                convertor = getattr(_convertor, "__name__", None)
        elif alias == list:
            try:
                is_array, convertor = True, args[0].__name__
            except Exception:
                """List[Any] should be implemented"""
        elif (
            hasattr(self._annotation, "__name__")
            and self._annotation.__name__ != "_empty"
        ):
            convertor = self._annotation.__name__
        else:
            assert not alias, f"Convertor for {self.name} unknown"
        return is_array, convertor


def get_handler_head_params(func: Callable[..., Any]) -> List[HeadParam]:
    signature = inspect.signature(func)
    results = []
    for k, v in signature.parameters.items():
        source = None
        if isinstance(v.default, (Query, Path, Cookie, Header)):
            source = v.default.in_.value
        elif v.annotation == WebSocket:
            continue
        elif v.default is v.empty:
            is_model = is_valid_body_model(v.annotation)
            is_affilated = get_annotation_affiliation(v.annotation)
            if not (is_model or is_affilated):
                source = "path_params"
        elif type(v.default) in (int, float, Decimal, str, bytes, type(None)):
            source = "path_params"

        if source is not None:
            results.append(HeadParam(name=k, value=v, source=source))

    return results


def get_annotation_affiliation(annotation: Any) -> Optional[Any]:
    """Helper for classifying affiliation of parameter

    :param annotation: annotation record
    :returns: classified value or None
    """
    args, alias = get_args(annotation), get_origin(annotation)
    # if alias and alias == list:
    annotation = args[0] if alias == list else annotation

    if annotation == Request:
        return "request"
    # elif isinstance(v.default, (Form, File)):
    #     return "form"
    return None


def is_valid_body_model(annotation: Any) -> bool:
    """Checks if the annotation is a valid type and includes dataclass"""
    valid = {typing.Union, type(None), list, set, tuple}

    models = []
    for i in get_types(annotation):
        if i in valid:
            continue
        if is_dataclass(i):
            models.append(i)
        else:
            return False
    return len(models) == 1


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
        elif isinstance(v.default, (Form, File)):
            param["kind"] = "form"
            param["model_class"] = annotation
        elif isinstance(v.default, Body):
            param["kind"] = "body"
        else:
            continue

        results.append(param)

    return results


def get_handler_request_fields(func: Callable[..., Any]) -> List[RequestField]:
    """Returns all fields that match as request schema"""
    signature = inspect.signature(func)
    results = []
    for name, v in signature.parameters.items():
        if is_valid_body_model(v.annotation):
            settings = v.default if isinstance(v.default, Body) else None
            field = RequestField(name, model=v.annotation, settings=settings)
            results.append(field)
    return results
