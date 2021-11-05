import asyncio
import email.message
import json
import re
import traceback
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
from squall.concurrency import run_in_threadpool
from squall.datastructures import Default, DefaultPlaceholder
from squall.dependencies.models import Dependant
from squall.dependencies.utils import solve_dependencies
from squall.exceptions import HTTPException, RequestValidationError
from squall.requests import Request
from squall.responses import JSONResponse, PlainTextResponse, Response
from squall.routing import APIRoute, APIWebSocketRoute
from squall.utils import get_value_or_default
from starlette.routing import iscoroutinefunction_or_partial
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocketClose


class NoMatchFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` and `.url_path_for(name, **path_params)`
    if no matching route exists.
    """


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


class Router:
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        routes: Optional[List[Union[APIRoute, APIWebSocketRoute]]] = None,
        route_class: Type[APIRoute] = APIRoute,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
    ) -> None:
        self._prefix = prefix
        self._tags = tags or []
        self._dependencies = list(dependencies or []) or []
        self._default_response_class = default_response_class
        self._route_class = route_class
        self._deprecated = deprecated
        self._include_in_schema = include_in_schema
        self._responses = responses or {}

        self._childs: List[Router] = []
        self._routes: List[Union[APIRoute, APIWebSocketRoute]] = routes or []

    def add_api_route(
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
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = JSONResponse,
        name: Optional[str] = None,
        route_class_override: Optional[Type[APIRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None
    ) -> None:
        route_class = route_class_override or self._route_class
        responses = responses or {}
        combined_responses = {**self._responses, **responses}
        current_response_class = get_value_or_default(
            response_class, self._default_response_class
        )
        current_tags = self._tags.copy()
        if tags:
            current_tags.extend(tags)
        current_dependencies = self._dependencies.copy()
        if dependencies:
            current_dependencies.extend(dependencies)
        route = route_class(
            path,
            endpoint=endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=current_tags,
            dependencies=current_dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=combined_responses,
            deprecated=deprecated or self._deprecated,
            methods=methods,
            operation_id=operation_id,
            include_in_schema=include_in_schema and self._include_in_schema,
            response_class=current_response_class,
            name=name,
            openapi_extra=openapi_extra,
        )
        self._routes.append(route)

    def add_ws_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        openapi_extra: Optional[Dict[str, Any]] = None
    ) -> None:
        route = APIWebSocketRoute(
            path,
            endpoint=endpoint,
            name=name,
        )
        self._routes.append(route)

    def include_router(self, router: "Router") -> None:
        self._childs.append(router)

    @property
    def routes(self) -> List[Union[APIRoute, APIWebSocketRoute]]:
        routes = []
        # Collect all nested routes, add current prefix
        # trough the route method and add to results
        for router in self._childs:
            for child_route in router.routes:
                routes.append(child_route)
        # Add prefix to own routes and also put them in results
        for own_route in self._routes:
            # Set own path, tags etc to `APIRoute.__init__` params.
            # Avoid duplication on further calls
            own_route.set_defaults()
            routes.append(own_route)
        # Add current prefix to the routes
        for route in routes:
            route.add_path_prefix(self._prefix)
        return routes


class RootRouter(Router):
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        routes: Optional[List[Union[APIRoute, APIWebSocketRoute]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = APIRoute,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
    ) -> None:
        # Need both, Router and Router
        super(RootRouter, self).__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            routes=routes,
            route_class=route_class,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
        )
        self._redirect_slashes = redirect_slashes
        self._default = default or self.not_found
        self._fast_path_route_http: Dict[str, Any] = {}
        self._fast_path_route_ws: Dict[str, Any] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        The main entry point to the Router class.
        """

    @staticmethod
    async def not_found(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            websocket_close = WebSocketClose()
            await websocket_close(scope, receive, send)
            return

        # If we're running inside a starlette application then raise an
        # exception, so that the configurable exception handler can deal with
        # returning the response. For plain ASGI apps, just return the response.
        if "app" in scope:
            raise HTTPException(status_code=404)
        else:
            response = PlainTextResponse("Not Found", status_code=404)
        await response(scope, receive, send)

    async def lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        started = False
        scope.get("app")
        await receive()
        try:
            # async with self.lifespan_context(app):
            await send({"type": "lifespan.startup.complete"})
            started = True
            await receive()
        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
        else:
            await send({"type": "lifespan.shutdown.complete"})

    @staticmethod
    def _get_fast_path_octets(path: str) -> List[str]:
        no_regex = re.sub(r"(\([^)]*\))", "*", path)
        no_format = re.sub(r"{([^}]*)}", "*", no_regex)
        return ["*" if "*" in i else i for i in no_format.strip("/").split("/")]

    def _add_fast_path_route(
        self, route: Union[APIRoute, APIWebSocketRoute], websocket: bool = False
    ) -> None:
        layer = self._fast_path_route_ws if websocket else self._fast_path_route_http

        for octet in self._get_fast_path_octets(route.path):
            if octet not in layer:
                layer[octet] = {}
                if octet != "*":
                    layer[octet]["*"] = {}
            layer = layer[octet]

        if "#routes#" not in layer:
            layer["#routes#"] = [] if websocket else {}

        if websocket:
            layer["#routes#"].append(route)
            return

        # List here for handling cases when single
        # octets path can have different patterns
        # /some/{number_item:int}
        # /some/{string_item:str}
        methods = getattr(route, "methods", [])
        for method in methods:
            if method not in layer["#routes#"]:
                layer["#routes#"][method] = []
            layer["#routes#"][method].append(route)

    def get_http_routes(self, method: str, path: str) -> List[APIRoute]:
        last = self._fast_path_route_http
        dyn = "*"
        try:
            for key in path.strip("/").split("/"):
                last = last.get(key) or last[dyn]
        except KeyError:
            return []
        routes: List[APIRoute] = last.get("#routes#", {}).get(method, [])
        return routes

    def get_ws_routes(self, path: str) -> List[APIWebSocketRoute]:
        last = self._fast_path_route_ws
        dyn = "*"
        try:
            for key in path.strip("/").split("/"):
                last = last.get(key) or last[dyn]
        except KeyError:
            return []
        return last.get("#routes#", [])

    def setup(self) -> None:
        for route in self.routes:
            if isinstance(route, APIRoute):
                self._add_fast_path_route(route, websocket=False)
            elif isinstance(route, APIWebSocketRoute):
                self._add_fast_path_route(route, websocket=True)
