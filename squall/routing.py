import asyncio
import enum
import functools
import inspect
import re
from decimal import Decimal
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    Type,
    Union,
)

from apischema import ValidationError, deserialization_method, serialization_method
from orjson import JSONDecodeError
from squall.bindings import RequestField, ResponseField
from squall.datastructures import Default, DefaultPlaceholder
from squall.exceptions import (
    HTTPException,
    RequestHeadValidationError,
    RequestPayloadValidationError,
    ResponsePayloadValidationError,
    WebSocketRequestValidationError,
)
from squall.requests import Request
from squall.responses import JSONResponse, Response
from squall.routing_.utils import (
    HeadParam,
    get_handler_body_params,
    get_handler_head_params,
    get_handler_request_fields,
)
from squall.types import ASGIApp
from squall.utils import generate_operation_id_for_path, get_callable_name
from squall.validators.head import Validator
from squall.websockets import WebSocket
from starlette.concurrency import run_in_threadpool
from starlette.convertors import CONVERTOR_TYPES, Convertor
from starlette.routing import websocket_session
from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.types import Receive, Scope, Send


class BaseRoute:
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[List[str]] = None,
    ) -> None:
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.methods = methods

    def matches(self, scope: Scope) -> Tuple[bool, Scope]:
        if match := self.path_regex.match(scope["path"]):
            return True, {"endpoint": self.endpoint, "path_params": match.groupdict()}
        return False, {}

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, BaseRoute)
            and self.path == other.path
            and self.endpoint == other.endpoint
            and self.methods == other.methods
        )

    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )

    def set_defaults(self) -> None:
        self.path = self._path_origin


class WebSocketRoute(BaseRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.head_params = get_handler_head_params(endpoint)
        self.head_validator = build_head_validator(self.head_params)
        self.name = get_callable_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema

        if inspect.isfunction(endpoint) or inspect.ismethod(endpoint):
            # Endpoint is function or method. Treat it as `func(websocket)`.
            self.app = websocket_session(
                get_websocket_handler(endpoint, head_validator=self.head_validator)
            )
        else:
            # Endpoint is a class. Treat it as ASGI.
            self.app = endpoint

        self.path_regex, self.path_format, self.param_convertors = compile_path(path)


class NoMatchFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` and `.url_path_for(name, **path_params)`
    if no matching route exists.
    """


# Match parameters in URL paths, eg. '{param}', and '{param:int}'
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


def compile_path(
    path: str,
) -> Tuple[Pattern[str], str, Dict[str, Convertor]]:
    """
    Given a path string, like: "/{username:str}", return a three-tuple
    of (regex, format, {param_name:convertor}).
    regex:      "/(?P<username>[^/]+)"
    format:     "/{username}"
    convertors: {"username": StringConvertor()}
    """
    path_regex = "^"
    path_format = ""
    duplicated_params = set()

    idx = 0
    param_convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")
        assert (
            convertor_type in CONVERTOR_TYPES
        ), f"Unknown path convertor '{convertor_type}'"
        convertor = CONVERTOR_TYPES[convertor_type]

        path_regex += re.escape(path[idx : match.start()])
        path_regex += f"(?P<{param_name}>{convertor.regex})"

        path_format += path[idx : match.start()]
        path_format += "{%s}" % param_name

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = convertor

        idx = match.end()

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    path_regex += re.escape(path[idx:]) + "$"
    path_format += path[idx:]

    return re.compile(path_regex), path_format, param_convertors


def get_http_handler(
    endpoint: Callable[..., Any],
    head_validator: Optional[Callable[..., Any]] = None,
    body_fields: Optional[List[Any]] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    request_field: Optional[RequestField] = None,
    request_deserializer: Optional[Callable[..., Any]] = None,
    response_deserializer: Optional[Callable[..., Any]] = None,
    response_serializer: Optional[Callable[..., Any]] = None,
) -> ASGIApp:
    is_coroutine = asyncio.iscoroutinefunction(endpoint)
    # is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    request_model = request_model_param = None
    if request_field is not None:
        request_model_param = request_field.name
        request_model = request_field.model

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)

        # Head validation
        if head_validator is not None:
            kwargs, errors = head_validator(request)
            if errors:
                raise RequestHeadValidationError(errors)
        else:
            kwargs = {}

        # Body fields and request object
        form = None
        try:
            if request_model is not None and request_deserializer is not None:
                body = await request.json()
                kwargs[request_model_param] = request_deserializer(body)

            if body_fields:
                form_missed = []
                for field in body_fields:
                    kind = field["kind"]
                    if kind == "request":
                        kwargs[field["name"]] = request
                    elif kind == "body":
                        ct = request.headers.get("content-type")
                        if ct is not None and ct[-4:] == "json":
                            kwargs[field["name"]] = await request.json()
                        else:
                            kwargs[field["name"]] = await request.body()
                    elif kind == "form":
                        if form is None:
                            form = await request.form()
                        value = form.get(field["name"])
                        if value is None:
                            form_missed.append(
                                {
                                    "loc": ["form", field["name"]],
                                    "msg": "field required",
                                }
                            )
                        else:
                            kwargs[field["name"]] = form.get(field["name"])
                if form_missed:
                    raise ValidationError.from_errors(form_missed)  # type: ignore
        except JSONDecodeError as e:
            raise RequestPayloadValidationError([str(e)])
        except ValidationError as e:
            raise RequestPayloadValidationError(e.messages, e.children)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

        if is_coroutine:
            raw_response = await endpoint(**kwargs)
        else:
            raw_response = await run_in_threadpool(endpoint, **kwargs)

        if isinstance(raw_response, Response):
            raw_response.request = request
            await raw_response(scope, receive, send)
            return

        response_args: Dict[str, Any] = {}

        # If status_code was set, use it, otherwise use the default from the
        # response class, in the case of redirect it's 307

        try:
            if response_deserializer is not None and response_serializer is not None:
                result = response_serializer(response_deserializer(raw_response))
            elif response_serializer is not None:
                result = response_serializer(raw_response)
            else:
                result = raw_response
        except ValidationError as e:
            raise ResponsePayloadValidationError(e.messages, e.children)
        except TypeError as e:
            raise ResponsePayloadValidationError([str(e)])

        if status_code is not None:
            response_args["status_code"] = status_code
        response = actual_response_class(result, **response_args)
        # Temporary solution in order to avoid header initialization
        response.request = request
        await response(scope, receive, send)

    return app


def get_websocket_handler(
    endpoint: Callable[..., Any],
    head_validator: Optional[Callable[..., Any]] = None,
) -> Callable[[WebSocket], Coroutine[Any, Any, Any]]:
    async def app(websocket: WebSocket) -> None:
        # Head validation
        if head_validator is not None:
            kwargs, errors = head_validator(websocket)
            if errors:
                await websocket.close(code=WS_1008_POLICY_VIOLATION)
                raise WebSocketRequestValidationError(errors)
        else:
            kwargs = {}
        await endpoint(websocket, **kwargs)

    return app


def build_head_validator(head_params: List[HeadParam]) -> Callable[..., Any]:
    v = Validator(
        args=["request"],
        convertors={
            "int": int,
            "float": float,
            "Decimal": Decimal,
            "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a),
            "bytes": lambda a: str(a).encode("utf-8") if type(a) != bytes else a,
        },
    )
    for param in head_params:
        v.add_rule(
            attribute=param.source,
            name=param.name,
            key=param.alias,
            check=param.validate,
            convert=param.convertor,
            as_list=param.is_array,
            default=param.default,
            **param.statements,
        )
    return v.build()


class Route(BaseRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.endpoint = endpoint
        self.name = get_callable_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema

        endpoint_handler = endpoint
        while isinstance(endpoint_handler, functools.partial):
            endpoint_handler = endpoint_handler.func
        if inspect.isfunction(endpoint_handler) or inspect.ismethod(endpoint_handler):
            # Endpoint is function or method. Treat it as `func(request) -> response`.
            self.app = get_http_handler(endpoint=endpoint)
            if methods is None:
                methods = ["GET"]
        else:
            # Endpoint is a class. Treat it as ASGI.
            self.app = endpoint

        if methods is None:
            self.methods = None
        else:
            self.methods = [method.upper() for method in methods]
            if self.methods is not None and "GET" in self.methods:
                self.methods.append("HEAD")

        self.path_regex, self.path_format, self.param_convertors = compile_path(path)


class APIRoute(Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        name: Optional[str] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        # normalise enums e.g. http.HTTPStatus
        if isinstance(status_code, enum.IntEnum):
            status_code = int(status_code)
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.head_params = get_handler_head_params(endpoint)
        self.head_validator = build_head_validator(self.head_params)

        self.body_fields = get_handler_body_params(endpoint)

        request_fields = get_handler_request_fields(endpoint)
        assert len(request_fields) < 2, "Only one request model allowed"
        self.request_field: Optional[RequestField] = None
        self.request_deserializer: Optional[Callable[..., Any]] = None
        if request_fields:
            self.request_field = request_fields[0]
            self.request_deserializer = deserialization_method(self.request_field.model)

        self.name = get_callable_name(endpoint) if name is None else name
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
        if methods is None:
            methods = ["GET"]
        self.methods = [method.upper() for method in methods]
        self.unique_id = generate_operation_id_for_path(
            name=self.name, path=self.path_format, method=list(methods)[0]
        )
        self.response_field: Optional[ResponseField] = None
        self.response_deserializer: Optional[Callable[..., Any]] = None
        self.response_serializer: Optional[Callable[..., Any]] = None

        endpoint_returns = inspect.signature(endpoint).return_annotation
        res_deserialize = True
        if response_model == endpoint_returns:
            res_deserialize = False
        # elif endpoint_returns != inspect._empty and response_model is None:
        #     response_model = endpoint_returns
        #     res_deserialize = False

        if response_model is not None:
            self.response_field = ResponseField(model=response_model)
            check_type_on_serialization = True
            if res_deserialize:
                self.response_deserializer = deserialization_method(
                    self.response_field.model
                )
                check_type_on_serialization = False
            self.response_serializer = serialization_method(
                self.response_field.model, check_type=check_type_on_serialization
            )

        self.status_code = status_code
        self.tags = tags or []
        self.summary = summary
        self.description = description or inspect.cleandoc(self.endpoint.__doc__ or "")
        self.description = self.description.split("\f")[0]
        self.response_description = response_description
        self.responses = responses or {}
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.include_in_schema = include_in_schema
        self.response_class = response_class

        assert callable(endpoint), "An endpoint must be a callable"

        self.app = self.get_route_handler()
        self.openapi_extra = openapi_extra

    def get_route_handler(self) -> ASGIApp:
        return get_http_handler(
            endpoint=self.endpoint,
            status_code=self.status_code,
            response_class=self.response_class,
            request_field=self.request_field,
            request_deserializer=self.request_deserializer,
            response_deserializer=self.response_deserializer,
            response_serializer=self.response_serializer,
            head_validator=self.head_validator,
            body_fields=self.body_fields,
        )
