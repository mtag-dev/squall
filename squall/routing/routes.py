import enum
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from apischema import deserialization_method, serialization_method
from squall import convertors
from squall.bindings import RequestField, ResponseField
from squall.datastructures import Default, DefaultPlaceholder
from squall.handlers import get_http_handler, get_websocket_handler
from squall.responses import JSONResponse, Response
from squall.routing.path import Path
from squall.routing.utils import (
    HeadParam,
    get_handler_body_params,
    get_handler_head_params,
    get_handler_request_fields,
)
from squall.types import ASGIApp
from squall.utils import generate_operation_id_for_path, get_callable_name
from squall.validators.head import Validator
from starlette.routing import websocket_session


class BaseRoute:
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[List[str]] = None,
    ) -> None:
        self.path = Path(path, endpoint)
        self.endpoint = endpoint
        self.methods = methods

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, BaseRoute)
            and self.path.path == other.path.path
            and self.endpoint == other.endpoint
            and self.methods == other.methods
        )


class WebSocketRoute(BaseRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.path = Path(path, endpoint)
        self.endpoint = endpoint
        self.name = get_callable_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.head_params: List[HeadParam] = []

    def get_route_handler(self) -> ASGIApp:
        self.head_params = get_handler_head_params(
            self.endpoint, self.path.get_path_params_from_handler()
        )
        head_validator = build_head_validator(self.head_params)

        if inspect.isfunction(self.endpoint) or inspect.ismethod(self.endpoint):
            # Endpoint is function or method. Treat it as `func(websocket)`.
            return websocket_session(
                get_websocket_handler(self.endpoint, head_validator=head_validator)
            )
        else:
            # Endpoint is a class. Treat it as ASGI.
            return self.endpoint


def build_head_validator(head_params: List[HeadParam]) -> Callable[..., Any]:
    con_db = {k: v.convert for k, v in convertors.database.convertors.items()}

    v = Validator(args=["request"], convertors=con_db)
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
        trace_internals: bool = False,
    ) -> None:
        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = Path(path, endpoint)
        self.endpoint = endpoint
        self.name = get_callable_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.trace_internals = trace_internals

        endpoint_handler = endpoint
        while isinstance(endpoint_handler, functools.partial):
            endpoint_handler = endpoint_handler.func
        if inspect.isfunction(endpoint_handler) or inspect.ismethod(endpoint_handler):
            # Endpoint is function or method. Treat it as `func(request) -> response`.
            self.app = get_http_handler(
                endpoint=endpoint, trace_internals=trace_internals
            )
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
        trace_internals: bool = False,
    ) -> None:
        # normalise enums e.g. http.HTTPStatus
        if isinstance(status_code, enum.IntEnum):
            status_code = int(status_code)
        self.path = Path(path, endpoint)
        self.endpoint = endpoint
        self.body_fields = get_handler_body_params(endpoint)

        request_fields = get_handler_request_fields(endpoint)
        assert len(request_fields) < 2, "Only one request model allowed"
        self.request_field: Optional[RequestField] = None
        self.request_deserializer: Optional[Callable[..., Any]] = None
        if request_fields:
            self.request_field = request_fields[0]
            self.request_deserializer = deserialization_method(self.request_field.model)

        self.name = get_callable_name(endpoint) if name is None else name
        if methods is None:
            methods = ["GET"]
        self.methods: List[str] = [method.upper() for method in methods]
        self.response_field: Optional[ResponseField] = None
        self.response_deserializer: Optional[Callable[..., Any]] = None
        self.response_serializer: Optional[Callable[..., Any]] = None

        endpoint_returns = inspect.signature(endpoint).return_annotation
        res_deserialize = response_model != endpoint_returns
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

        self.openapi_extra = openapi_extra
        self.head_params: List[HeadParam] = []
        self.trace_internals = trace_internals

    @property
    def unique_id(self) -> str:
        return generate_operation_id_for_path(
            name=self.name, path=self.path.schema_path, method=self.methods[0]
        )

    def get_route_handler(self) -> ASGIApp:
        self.head_params = get_handler_head_params(
            self.endpoint, self.path.get_path_params_from_handler()
        )
        head_validator = build_head_validator(self.head_params)

        return get_http_handler(
            endpoint=self.endpoint,
            status_code=self.status_code,
            response_class=self.response_class,
            request_field=self.request_field,
            request_deserializer=self.request_deserializer,
            response_deserializer=self.response_deserializer,
            response_serializer=self.response_serializer,
            head_validator=head_validator,
            body_fields=self.body_fields,
            trace_internals=self.trace_internals,
        )
