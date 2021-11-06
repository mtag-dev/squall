import typing
from typing import Any, Callable, Coroutine, Dict, List, Optional, Sequence, Type, Union

from squall import router
from squall.concurrency import AsyncExitStack
from squall.datastructures import Default
from squall.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from squall.exceptions import RequestValidationError
from squall.lifespan import lifespan
from squall.logger import logger
from squall.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from squall.openapi.utils import get_openapi
from squall.params import Depends
from squall.requests import Request
from squall.responses import HTMLResponse, JSONResponse, Response
from starlette.datastructures import State
from starlette.exceptions import ExceptionMiddleware, HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Receive, Scope, Send


class Squall:
    def __init__(
        self,
        *,
        debug: bool = False,
        routes: Optional[List[BaseRoute]] = None,
        title: str = "Squall",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[
            Dict[
                Union[int, Type[Exception]],
                Callable[[Request, Any], Coroutine[Any, Any, Response]],
            ]
        ] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Dict[str, Union[str, Any]]] = None,
        license_info: Optional[Dict[str, Union[str, Any]]] = None,
        openapi_prefix: str = "",
        root_path: str = "",
        root_path_in_servers: bool = True,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        **extra: Any,
    ) -> None:
        self._debug: bool = debug
        self.state: State = State()

        self.router: router.RootRouter = router.RootRouter(
            routes=routes,
            default_response_class=default_response_class,
            dependencies=dependencies,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            dependency_overrides_provider=self,
        )
        # Router methods linking for better user experience like having
        # @app.get(...) instead of @app.get(...)
        self.get = self.router.get
        self.put = self.router.put
        self.post = self.router.post
        self.delete = self.router.delete
        self.options = self.router.options
        self.head = self.router.head
        self.patch = self.router.patch
        self.trace = self.router.trace
        self.include_router = self.router.include_router
        self.routes = self.router.routes
        self.add_route = self.router.add_route

        self.exception_handlers: Dict[
            Union[int, Type[Exception]],
            Callable[[Request, Any], Coroutine[Any, Any, Response]],
        ] = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self.exception_handlers.setdefault(HTTPException, http_exception_handler)
        self.exception_handlers.setdefault(
            RequestValidationError, request_validation_exception_handler
        )

        self.user_middleware: List[Middleware] = (
            [] if middleware is None else list(middleware)
        )
        self.middleware_stack: ASGIApp = self.build_middleware_stack()

        self.title = title
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.servers = servers or []
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        # TODO: remove when discarding the openapi_prefix parameter
        if openapi_prefix:
            logger.warning(
                '"openapi_prefix" has been deprecated in favor of "root_path", which '
                "follows more closely the ASGI standard, is simpler, and more "
                "automatic. Check the docs at "
                "https://squall.mtag.dev/advanced/sub-applications/"
            )
        self.root_path = root_path or openapi_prefix
        self.root_path_in_servers = root_path_in_servers
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.extra = extra
        self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}

        self.openapi_version = "3.0.2"

        if self.openapi_url:
            assert self.title, "A title must be provided for OpenAPI, e.g.: 'My API'"
            assert self.version, "A version must be provided for OpenAPI, e.g.: '2.1.0'"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        self.on_startup = []
        if on_startup:
            self.on_startup.extend(list(on_startup))
        self.on_shutdown = [] if on_shutdown is None else list(on_shutdown)

        self.setup()

    def build_middleware_stack(self) -> ASGIApp:
        debug = self.debug
        error_handler = None
        exception_handlers = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
            + self.user_middleware
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=debug
                )
            ]
        )

        app = self.router
        for cls, options in reversed(middleware):
            app = cls(app=app, **options)
        return app

    def exception_handler(
        self, exc_class_or_status_code: typing.Union[int, typing.Type[Exception]]
    ) -> typing.Callable:
        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = value
        self.middleware_stack = self.build_middleware_stack()

    def add_event_handler(
        self, event: str, handler: Union[Callable, Coroutine]
    ) -> None:
        if event == "startup":
            self.on_startup.append(handler)
        elif event == "shutdown":
            self.on_shutdown.append(handler)

    def on_event(self, event_type: str) -> typing.Callable:
        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_event_handler(event_type, func)
            return func

        return decorator

    def add_middleware(self, middleware_class: type, **options: typing.Any) -> None:
        self.user_middleware.insert(0, Middleware(middleware_class, **options))
        self.middleware_stack = self.build_middleware_stack()

    def add_exception_handler(
        self,
        exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
        handler: typing.Callable,
    ) -> None:
        self.exception_handlers[exc_class_or_status_code] = handler
        self.middleware_stack = self.build_middleware_stack()

    def openapi(self) -> Dict[str, Any]:
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=self.routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )
        return self.openapi_schema

    def setup(self) -> None:
        if self.openapi_url:
            urls = (server_data.get("url") for server_data in self.servers)
            server_urls = {url for url in urls if url}

            async def openapi(req: Request) -> JSONResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                if root_path not in server_urls:
                    if root_path and self.root_path_in_servers:
                        self.servers.insert(0, {"url": root_path})
                        server_urls.add(root_path)
                return JSONResponse(
                    self.openapi().dict(exclude_unset=True, by_alias=True)  # type: ignore
                )

            self.router.add_api_route(
                self.openapi_url, openapi, include_in_schema=False
            )
        if self.openapi_url and self.docs_url:

            async def swagger_ui_html(req: Request) -> HTMLResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                openapi_url = root_path + self.openapi_url
                oauth2_redirect_url = self.swagger_ui_oauth2_redirect_url
                if oauth2_redirect_url:
                    oauth2_redirect_url = root_path + oauth2_redirect_url
                return get_swagger_ui_html(
                    openapi_url=openapi_url,
                    title=self.title + " - Swagger UI",
                    oauth2_redirect_url=oauth2_redirect_url,
                    init_oauth=self.swagger_ui_init_oauth,
                )

            self.router.add_api_route(
                self.docs_url, swagger_ui_html, include_in_schema=False
            )

            if self.swagger_ui_oauth2_redirect_url:

                async def swagger_ui_redirect(req: Request) -> HTMLResponse:
                    return get_swagger_ui_oauth2_redirect_html()

                self.router.add_api_route(
                    self.swagger_ui_oauth2_redirect_url,
                    swagger_ui_redirect,
                    include_in_schema=False,
                )
        if self.openapi_url and self.redoc_url:

            async def redoc_html(req: Request) -> HTMLResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                openapi_url = root_path + self.openapi_url
                return get_redoc_html(
                    openapi_url=openapi_url, title=self.title + " - ReDoc"
                )

            self.router.add_api_route(
                self.redoc_url, redoc_html, include_in_schema=False
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.root_path:
            scope["root_path"] = self.root_path

        scope["app"] = self
        if scope["type"] == "lifespan":
            await lifespan(self.on_startup, self.on_shutdown, scope, receive, send)
            return

        async with AsyncExitStack() as stack:
            scope["squall_astack"] = stack
            await self.middleware_stack(scope, receive, send)

    def middleware(self, middleware_type: str) -> typing.Callable:
        assert (
            middleware_type == "http"
        ), 'Currently only middleware("http") is supported.'

        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func

        return decorator
