from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)

import squall_router
from squall import convertors
from squall.datastructures import Default
from squall.exceptions import HTTPException
from squall.responses import JSONResponse, PlainTextResponse, Response
from squall.routing.routes import APIRoute, WebSocketRoute
from squall.staticfiles import StaticFiles
from squall.types import ASGIApp, DecoratedCallable, Receive, Scope, Send
from squall.utils import get_value_or_default
from starlette.websockets import WebSocketClose

PLACEHOLDER_DYNAMIC = "*"
PLACEHOLDER_LOCATION = "**"


class Router:
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        routes: Optional[List[Union[APIRoute, WebSocketRoute]]] = None,
        route_class: Type[APIRoute] = APIRoute,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        trace_internals: bool = False,
    ) -> None:
        self._prefix = prefix
        self._tags = tags or []
        self._default_response_class = default_response_class
        self._deprecated = deprecated
        self._include_in_schema = include_in_schema
        self._responses = responses or {}
        self._routes: List[Union[APIRoute, WebSocketRoute]] = routes or []

        self.trace_internals = trace_internals
        self.route_class = route_class

    def add_api_route(
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
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = JSONResponse,
        name: Optional[str] = None,
        route_class_override: Optional[Type[APIRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        route_class = route_class_override or self.route_class
        responses = responses or {}
        combined_responses = {**self._responses, **responses}
        current_response_class = get_value_or_default(
            response_class, self._default_response_class
        )
        current_tags = self._tags.copy()
        if tags:
            current_tags.extend(tags)

        route = route_class(
            self._prefix + path,
            endpoint=endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=current_tags,
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
            trace_internals=self.trace_internals,
        )
        self.route_register(route)

    def add_route(
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
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Response,
        name: Optional[str] = None,
        route_class_override: Optional[Type[APIRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        route_class = route_class_override or self.route_class
        responses = responses or {}
        combined_responses = {**self._responses, **responses}
        current_response_class = get_value_or_default(
            response_class, self._default_response_class
        )
        current_tags = self._tags.copy()
        if tags:
            current_tags.extend(tags)

        route = route_class(
            self._prefix + path,
            endpoint=endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=current_tags,
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
        self.route_register(route)

    def route_register(self, route: Union[APIRoute, WebSocketRoute]) -> None:
        self._routes.append(route)

    def add_api(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Registrates API endpoint.

        Examples:
            >>> app = Squall()
            >>>
            >>> @app.add_api("/users/{username}", methods=["GET"])
            >>> async def read_user(username: str):
            >>>     return {"username": username}
        """

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_api_route(
                path,
                func,
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                methods=methods,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                openapi_extra=openapi_extra,
            )
            return func

        return decorator

    def add_ws_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
    ) -> None:
        route = WebSocketRoute(
            self._prefix + path,
            endpoint=endpoint,
            name=name,
        )
        self.route_register(route)

    def websocket(
        self, path: str, name: Optional[str] = None
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Registrates WebSocket endpoint.

        Examples:
            >>> app = Squall()
            >>>
            >>> @app.websocket("/ws")
            >>> async def websocket(websocket: WebSocket):
            >>>     await websocket.accept()
            >>>     await websocket.send_json({"msg": "Hello WebSocket"})
            >>>     await websocket.close()
        """

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_ws_route(path, func, name=name)
            return func

        return decorator

    def include_router(self, router: "Router") -> None:
        """Includes child router

        Examples:
            >>> from squall import Squall, Router
            >>> app = Squall()
            >>> router = Router(prefix="/api")
            >>>
            >>> @router.get("/users/{username}")
            >>> async def read_user(username: str):
            >>>     return {"username": username}
            >>>
            >>> app.include_router(router)
        """
        for route in router.routes:
            route.path.append_left(self._prefix)
            # route.add_path_prefix(self._prefix)
            self.route_register(route)

    @property
    def routes(self) -> List[Union[APIRoute, WebSocketRoute]]:
        return self._routes

    def get(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["GET"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def put(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["PUT"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def post(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["POST"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def delete(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["DELETE"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def options(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["OPTIONS"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def head(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["HEAD"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def patch(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["PATCH"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )

    def trace(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:

        return self.add_api(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=["TRACE"],
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
        )


class RootRouter(Router):
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        routes: Optional[List[Union[APIRoute, WebSocketRoute]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = APIRoute,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        trace_internals: bool = False,
        ignore_trailing_slashes: bool = False,
    ) -> None:
        # Need both, Router and Router
        super(RootRouter, self).__init__(
            prefix=prefix,
            tags=tags,
            default_response_class=default_response_class,
            routes=routes,
            route_class=route_class,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            trace_internals=trace_internals,
        )
        self.redirect_slashes = redirect_slashes
        self.default = default or self.not_found
        self._fast_path_route_http: Dict[str, Any] = {}
        self._fast_path_route_ws: Dict[str, Any] = {}
        self._router = squall_router.Router()
        if ignore_trailing_slashes:
            self._router.set_ignore_trailing_slashes()
        for convertor in convertors.database.convertors.values():
            self._router.add_validator(convertor.alias, convertor.regex)
        self._last_handler_id = 0
        self._handlers: Dict[int, ASGIApp] = {}
        self.ignore_trailing_slashes = ignore_trailing_slashes

    def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[Any]:
        """
        The main entry point to the Router class.
        """
        if "router" not in scope:
            scope["router"] = self

        routes: Sequence[Union[APIRoute, WebSocketRoute]]

        if scope["type"] == "http":
            method = scope["method"]
        elif scope["type"] == "websocket":
            method = "WS"
        else:
            assert False, f"RootRouter doesn't allow scope type: {scope['type']}"

        if resolved := self._router.resolve(method, scope["path"]):
            handler_id, params = resolved
            if handler := self._handlers.get(handler_id):
                scope["path_params"] = dict(params)
                return handler(scope, receive, send)

        return self.default(scope, receive, send)

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

    def route_register(self, route: Union[APIRoute, WebSocketRoute]) -> None:
        methods = getattr(route, "methods", ["WS"])
        if self.ignore_trailing_slashes:
            route.path.strip_trailing_slash()

        for method in methods:
            self._router.add_route(
                method, route.path.router_path, self._last_handler_id
            )
            self._handlers[self._last_handler_id] = route.get_route_handler()
            self._last_handler_id += 1

        self._routes.append(route)

    def add_location(
        self, path: str, handler: ASGIApp, name: str, method: str = "GET"
    ) -> None:
        def _static(scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
            if scope["path"].startswith(path):
                scope["path"] = scope["path"][len(path) :]
            return handler(scope, receive, send)

        _handler = _static if isinstance(handler, StaticFiles) else handler
        self._handlers[self._last_handler_id] = _handler
        self._router.add_location(method, path, self._last_handler_id)
        self._last_handler_id += 1
