import enum
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from squall import params
from squall.datastructures import Default
from squall.exceptions import HTTPException
from squall.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from squall.routing import APIRoute, APIWebSocketRoute
from squall.types import ASGIApp, DecoratedCallable, Receive, Scope, Send
from squall.utils import get_value_or_default
from starlette.datastructures import URL
from starlette.routing import Match as SlMatch
from starlette.websockets import WebSocketClose


class PathPlaceholder(enum.Enum):
    DYNAMIC = "*"
    LOCATION = "**"


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
        dependency_overrides_provider: Optional[Any] = None,
    ) -> None:
        self._prefix = prefix
        self._tags = tags or []
        self._dependencies = list(dependencies or []) or []
        self._default_response_class = default_response_class
        self._route_class = route_class
        self._deprecated = deprecated
        self._include_in_schema = include_in_schema
        self._responses = responses or {}
        self.dependency_overrides_provider = dependency_overrides_provider

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
        openapi_extra: Optional[Dict[str, Any]] = None,
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
            self._prefix + path,
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
            dependency_overrides_provider=self.dependency_overrides_provider,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
            self._prefix + path,
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
            dependency_overrides_provider=self.dependency_overrides_provider,
        )
        self.route_register(route)

    def route_register(self, route: Union[APIRoute, APIWebSocketRoute]) -> None:
        self._routes.append(route)

    def api_route(
        self,
        path: str,
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
        methods: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_api_route(
                path,
                func,
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
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
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        route = APIWebSocketRoute(
            self._prefix + path,
            endpoint=endpoint,
            name=name,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )
        self.route_register(route)

    def websocket_route(
        self, path: str, name: Optional[str] = None
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_ws_route(path, func, name=name)
            return func

        return decorator

    def include_router(self, router: "Router") -> None:
        for route in router.routes:
            route.add_path_prefix(self._prefix)
            self.route_register(route)

    @property
    def routes(self) -> List[Union[APIRoute, APIWebSocketRoute]]:
        return self._routes

    def get(
        self,
        path: str,
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
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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
        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
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

        return self.api_route(
            path=path,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
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
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        routes: Optional[List[Union[APIRoute, APIWebSocketRoute]]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        route_class: Type[APIRoute] = APIRoute,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        dependency_overrides_provider: Optional[Any] = None,
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
            dependency_overrides_provider=dependency_overrides_provider,
        )
        self.redirect_slashes = redirect_slashes
        self.default = default or self.not_found
        self._fast_path_route_http: Dict[str, Any] = {}
        self._fast_path_route_ws: Dict[str, Any] = {}
        # self.lifespan_context: Callable[[Any], AsyncContextManager] = RouterLifespan(self)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        The main entry point to the Router class.
        """
        if "router" not in scope:
            scope["router"] = self

        routes: Sequence[Union[APIRoute, APIWebSocketRoute]]
        if scope["type"] == "http":
            routes, _locations = self.get_http_routes(scope["method"], scope["path"])
        elif scope["type"] == "websocket":
            routes, _ = self.get_ws_routes(scope["path"]), []
        else:
            assert False, f"RootRouter doesn't allow scope type: {scope['type']}"

        for route in routes:
            # Determine if any route matches the incoming scope,
            # and hand over to the matching route if found.
            match, child_scope = route.matches(scope)
            if match == SlMatch.FULL:
                scope.update(child_scope)
                await route.handle(scope, receive, send)
                return

        # for location in reversed(_locations):
        #     match, child_scope = location.matches(scope)
        #     if match == SlMatch.FULL:
        #         scope.update(child_scope)
        #         await location.handle(scope, receive, send)
        #         return

        if scope["type"] == "http" and self.redirect_slashes and scope["path"] != "/":
            redirect_scope = dict(scope)
            if scope["path"].endswith("/"):
                redirect_scope["path"] = redirect_scope["path"].rstrip("/")
            else:
                redirect_scope["path"] = redirect_scope["path"] + "/"

            routes, _ = self.get_http_routes(
                redirect_scope["method"], redirect_scope["path"]
            )
            for route in routes:
                match, child_scope = route.matches(redirect_scope)
                if match != SlMatch.NONE:
                    redirect_url = URL(scope=redirect_scope)
                    response = RedirectResponse(url=str(redirect_url))
                    await response(scope, receive, send)
                    return

        await self.default(scope, receive, send)

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

    @staticmethod
    def _get_fast_path_octets(path: str) -> List[str]:
        no_regex = re.sub(r"(\([^)]*\))", PathPlaceholder.DYNAMIC.value, path)
        no_format = re.sub(r"{([^}]*)}", PathPlaceholder.DYNAMIC.value, no_regex)
        result = []
        for i in no_format.strip("/").split("/"):
            value = (
                PathPlaceholder.DYNAMIC.value
                if PathPlaceholder.DYNAMIC.value in i
                else i
            )
            result.append(value)
        return result

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

    def route_register(self, route: Union[APIRoute, APIWebSocketRoute]) -> None:
        if isinstance(route, APIRoute):
            self._add_fast_path_route(route, websocket=False)
        elif isinstance(route, APIWebSocketRoute):
            self._add_fast_path_route(route, websocket=True)
        self._routes.append(route)

    def get_http_routes(
        self, method: str, path: str
    ) -> Tuple[List[APIRoute], List[APIRoute]]:
        last = self._fast_path_route_http
        locations = []
        try:
            for key in path.strip("/").split("/"):
                last = last.get(key) or last[PathPlaceholder.DYNAMIC.value]
                if PathPlaceholder.LOCATION.value in last:
                    locations.append(last[PathPlaceholder.LOCATION.value])
        except KeyError:
            return [], locations
        routes: List[APIRoute] = last.get("#routes#", {}).get(method, [])
        return routes, locations

    def get_ws_routes(self, path: str) -> List[APIWebSocketRoute]:
        last = self._fast_path_route_ws
        try:
            for key in path.strip("/").split("/"):
                last = last.get(key) or last[PathPlaceholder.DYNAMIC.value]
        except KeyError:
            return []
        return last.get("#routes#", [])
