import asyncio
import email.message
import enum
import inspect
import json
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)

from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.fields import ModelField, Undefined
from squall import params
from squall.datastructures import Default, DefaultPlaceholder
from squall.dependencies.models import Dependant
from squall.dependencies.utils import (
    get_body_field,
    get_dependant,
    get_parameterless_sub_dependant,
    solve_dependencies,
)
from squall.exceptions import RequestValidationError, WebSocketRequestValidationError
from squall.openapi.constants import STATUS_CODES_WITH_NO_BODY
from squall.requests import Request
from squall.responses import JSONResponse, Response
from squall.utils import (
    create_cloned_field,
    create_response_field,
    generate_operation_id_for_path,
)
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.routing import BaseRoute as SlBaseRoute
from starlette.routing import Mount as Mount  # noqa
from starlette.routing import Route as SlRoute
from starlette.routing import WebSocketRoute as SlWebSocketRoute
from starlette.routing import (
    compile_path,
    get_name,
    iscoroutinefunction_or_partial,
    websocket_session,
)
from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket


class WebSocketRoute(SlWebSocketRoute):
    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path


class NoMatchFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` and `.url_path_for(name, **path_params)`
    if no matching route exists.
    """


#
# class Match(enum.Enum):
#     NONE = 0
#     PARTIAL = 1
#     FULL = 2
#
#
# class Event(enum.Enum):
#     STARTUP = "startup"
#     SHUTDOWN = "shutdown"


def request_response(func: Callable[..., Any]) -> ASGIApp:
    """
    Takes a function or coroutine `func(request) -> response`,
    and returns an ASGI application.
    """
    is_coroutine = iscoroutinefunction_or_partial(func)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)
        if is_coroutine:
            response = await func(request)
        else:
            response = await run_in_threadpool(func, request)
        await response(scope, receive, send)

    return app


async def run_endpoint_function(
    *, dependant: Dependant, values: Dict[str, Any], is_coroutine: bool
) -> Any:
    # Only called by get_request_handler. Has been split into its own function to
    # facilitate profiling endpoints, since inner functions are harder to profile.
    assert dependant.call is not None, "dependant.call must be a function"

    if is_coroutine:
        return await dependant.call(**values)
    else:
        return await run_in_threadpool(dependant.call, **values)


def get_request_handler(
    dependant: Dependant,
    body_field: Optional[ModelField] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    dependency_overrides_provider: Optional[Any] = None,
    response_field: Optional[ModelField] = None,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    assert dependant.call is not None, "dependant.call must be a function"
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(request: Request) -> Response:
        try:
            body: Any = None
            if body_field:
                if is_body_form:
                    body = await request.form()
                else:
                    body_bytes = await request.body()
                    if body_bytes:
                        json_body: Any = Undefined
                        content_type_value = request.headers.get("content-type")
                        if not content_type_value:
                            json_body = await request.json()
                        else:
                            message = email.message.Message()
                            message["content-type"] = content_type_value
                            if message.get_content_maintype() == "application":
                                subtype = message.get_content_subtype()
                                if subtype == "json" or subtype.endswith("+json"):
                                    json_body = await request.json()
                        if json_body != Undefined:
                            body = json_body
                        else:
                            body = body_bytes
        except json.JSONDecodeError as e:
            raise RequestValidationError([ErrorWrapper(e, ("body", e.pos))], body=e.doc)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e
        solved_result = await solve_dependencies(
            request=request,
            dependant=dependant,
            body=body,
            dependency_overrides_provider=dependency_overrides_provider,
        )
        values, errors, background_tasks, sub_response, _ = solved_result
        if errors:
            raise RequestValidationError(errors, body=body)
        else:
            raw_response = await run_endpoint_function(
                dependant=dependant, values=values, is_coroutine=is_coroutine
            )
            if isinstance(raw_response, Response):
                if raw_response.background is None:
                    raw_response.background = background_tasks
                return raw_response

            response_args: Dict[str, Any] = {"background": background_tasks}
            # If status_code was set, use it, otherwise use the default from the
            # response class, in the case of redirect it's 307
            if response_field is not None:
                response_value, response_errors = response_field.validate(
                    raw_response, {}, loc=("response",)
                )
                if response_errors:
                    raise ValidationError([response_errors], response_field.type_)
            else:
                response_value = raw_response

            if status_code is not None:
                response_args["status_code"] = status_code
            response = actual_response_class(response_value, **response_args)
            response.headers.raw.extend(sub_response.headers.raw)
            if sub_response.status_code:
                response.status_code = sub_response.status_code
            return response

    return app


def get_websocket_app(
    dependant: Dependant, dependency_overrides_provider: Optional[Any] = None
) -> Callable[[WebSocket], Coroutine[Any, Any, Any]]:
    async def app(websocket: WebSocket) -> None:
        solved_result = await solve_dependencies(
            request=websocket,
            dependant=dependant,
            dependency_overrides_provider=dependency_overrides_provider,
        )
        values, errors, _, _2, _3 = solved_result
        if errors:
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise WebSocketRequestValidationError(errors)
        assert dependant.call is not None, "dependant.call must be a function"
        await dependant.call(**values)

    return app


class Route(SlRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        super(Route, self).__init__(
            path,
            endpoint,
            methods=methods,  # type: ignore
            name=name,  # type: ignore
            include_in_schema=include_in_schema,
        )


class APIWebSocketRoute(WebSocketRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
        dependency_overrides_provider: Optional[Any] = None,
    ) -> None:
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.name = get_name(endpoint) if name is None else name
        self.dependant = get_dependant(path=path, call=self.endpoint)
        self.app = websocket_session(
            get_websocket_app(
                dependant=self.dependant,
                dependency_overrides_provider=dependency_overrides_provider,
            )
        )
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)

    def set_defaults(self) -> None:
        self.path = self._path_origin

    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )


class APIRoute(Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        dependency_overrides_provider: Optional[Any] = None,
        callbacks: Optional[List[SlBaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        # normalise enums e.g. http.HTTPStatus
        if isinstance(status_code, enum.IntEnum):
            status_code = int(status_code)
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.name = get_name(endpoint) if name is None else name
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
        if methods is None:
            methods = ["GET"]
        self.methods: Set[str] = {method.upper() for method in methods}
        self.unique_id = generate_operation_id_for_path(
            name=self.name, path=self.path_format, method=list(methods)[0]
        )
        self.response_model = response_model
        if self.response_model:
            assert (
                status_code not in STATUS_CODES_WITH_NO_BODY
            ), f"Status code {status_code} must not have a response body"
            response_name = "Response_" + self.unique_id
            self.response_field = create_response_field(
                name=response_name, type_=self.response_model
            )
            # Create a clone of the field, so that a Pydantic submodel is not returned
            # as is just because it's an instance of a subclass of a more limited class
            # e.g. UserInDB (containing hashed_password) could be a subclass of User
            # that doesn't have the hashed_password. But because it's a subclass, it
            # would pass the validation and be returned as is.
            # By being a new field, no inheritance will be passed as is. A new model
            # will be always created.
            self.secure_cloned_response_field: Optional[
                ModelField
            ] = create_cloned_field(self.response_field)
        else:
            self.response_field = None  # type: ignore
            self.secure_cloned_response_field = None
        self.status_code = status_code
        self.tags = tags or []
        self.dependencies = list(dependencies) if dependencies else []
        self.summary = summary
        self.description = description or inspect.cleandoc(self.endpoint.__doc__ or "")
        # if a "form feed" character (page break) is found in the description text,
        # truncate description text to the content preceding the first "form feed"
        self.description = self.description.split("\f")[0]
        self.response_description = response_description
        self.responses = responses or {}
        response_fields = {}
        for additional_status_code, response in self.responses.items():
            assert isinstance(response, dict), "An additional response must be a dict"
            model = response.get("model")
            if model:
                assert (
                    additional_status_code not in STATUS_CODES_WITH_NO_BODY
                ), f"Status code {additional_status_code} must not have a response body"
                response_name = f"Response_{additional_status_code}_{self.unique_id}"
                response_field = create_response_field(name=response_name, type_=model)
                response_fields[additional_status_code] = response_field
        if response_fields:
            self.response_fields: Dict[Union[int, str], ModelField] = response_fields
        else:
            self.response_fields = {}
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.include_in_schema = include_in_schema
        self.response_class = response_class

        assert callable(endpoint), "An endpoint must be a callable"
        self.dependant = get_dependant(path=self.path_format, call=self.endpoint)
        for depends in self.dependencies[::-1]:
            self.dependant.dependencies.insert(
                0,
                get_parameterless_sub_dependant(depends=depends, path=self.path_format),
            )
        self.body_field = get_body_field(dependant=self.dependant, name=self.unique_id)
        self.dependency_overrides_provider = dependency_overrides_provider
        self.callbacks = callbacks
        self.app = request_response(self.get_route_handler())
        self.openapi_extra = openapi_extra

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        return get_request_handler(
            dependant=self.dependant,
            body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class,
            dependency_overrides_provider=self.dependency_overrides_provider,
            response_field=self.response_field,
        )

    def set_defaults(self) -> None:
        self.path = self._path_origin

    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
