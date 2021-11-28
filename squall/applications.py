from asyncio import iscoroutinefunction
import typing
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union

from squall.concurrency import run_in_threadpool

from squall import router
from squall.datastructures import Default
from squall.errors import get_default_debug_response
from squall.exception_handlers import (
    http_exception_handler,
    request_head_validation_exception_handler,
    request_payload_validation_exception_handler,
)
from squall.exceptions import RequestHeadValidationError, RequestPayloadValidationError
from squall.lifespan import LifespanContext, lifespan
from squall.logger import logger
from squall.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from squall.openapi.utils import get_openapi

from squall.requests import Request
from squall.responses import HTMLResponse, JSONResponse, Response, PlainTextResponse
from squall.routing import APIRoute, APIWebSocketRoute
from squall.types import AnyFunc, ASGIApp, Receive, Scope, Send
from squall.exceptions import HTTPException
from starlette.datastructures import State
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware


class Squall:
    _default_error_response = PlainTextResponse("Internal Server Error", status_code=500)

    def __init__(
        self,
        *,
        debug: bool = False,
        routes: Optional[Optional[List[Union[APIRoute, APIWebSocketRoute]]]] = None,
        title: str = "Squall",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[Dict[Union[int, Type[Exception]], AnyFunc]] = None,
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
        self.debug: bool = debug
        self.state: State = State()

        self.router: router.RootRouter = router.RootRouter(
            routes=routes,
            default_response_class=default_response_class,
            # dependencies=dependencies,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            # dependency_overrides_provider=self,
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
        self.add_api = self.router.add_api
        self.add_api_route = self.router.add_api_route
        self.websocket = self.router.websocket

        self.exception_handlers: Dict[Union[int, Type[Exception]], AnyFunc] = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self.exception_handlers.setdefault(HTTPException, http_exception_handler)
        self.exception_handlers.setdefault(
            RequestPayloadValidationError, request_payload_validation_exception_handler
        )
        self.exception_handlers.setdefault(
            RequestHeadValidationError, request_head_validation_exception_handler
        )

        self.user_middleware: List[Middleware] = (
            [] if middleware is None else list(middleware)
        )
        self.middleware_stack: ASGIApp = self._build_middleware_stack()

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
        # self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}

        self.openapi_version = "3.0.2"

        if self.openapi_url:
            assert self.title, "A title must be provided for OpenAPI, e.g.: 'My API'"
            assert self.version, "A version must be provided for OpenAPI, e.g.: '2.1.0'"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        self.on_startup = [] if on_startup is None else list(on_startup)
        self.on_shutdown = [] if on_shutdown is None else list(on_shutdown)
        self.lifespan_ctx = LifespanContext(self.on_startup, self.on_shutdown)

        self._setup()

    def add_event_handler(self, event: str, handler: AnyFunc) -> None:
        """Registrates event hooks.
        There are two evens availiable: startup, shutdown

        Examples:
            >>> app = Squall()
            >>>
            >>> def some_func_to_call_on_startup():
            >>>     pass
            >>>
            >>> async def some_func_to_call_on_shutdown():
            >>>     pass
            >>>
            >>> app.add_event_handler("startup", some_func_to_call_on_startup)
            >>> app.add_event_handler("shutdown", some_func_to_call_on_shutdown)
        """
        if event == "startup":
            self.on_startup.append(handler)
        elif event == "shutdown":
            self.on_shutdown.append(handler)

    def on_event(self, event_type: str) -> typing.Callable[..., Any]:
        """Decorator for event hook registration

        Examples:
            >>> app = Squall()
            >>>
            >>> @app.on_event("startup")
            >>> def some_func_to_call_on_startup():
            >>>     pass
            >>>
            >>> @app.on_event("shutdown")
            >>> async def some_func_to_call_on_shutdown():
            >>>     pass
        """

        def decorator(func: AnyFunc) -> AnyFunc:
            self.add_event_handler(event_type, func)
            return func

        return decorator

    def add_exception_handler(
        self,
        exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
        handler: typing.Callable[..., Any],
    ) -> None:
        """Adds exception handler.

        Examples:
            >>> app = Squall()
            >>>
            >>> class BackEndException(Exception): pass
            >>>
            >>> async def backend_exception_handler():
            >>>     return JSONResponse(
            >>>         status_code=500,
            >>>         content={"message": "BackEnd error"}
            >>>     )
            >>>
            >>> app.add_exception_handler(BackEndException, backend_exception_handler)
        """
        self.exception_handlers[exc_class_or_status_code] = handler

    def exception_handler(
        self, exc_class_or_status_code: typing.Union[int, typing.Type[Exception]]
    ) -> typing.Callable[..., Any]:
        """Decorator for exception handler registration.

        Examples:
            >>> app = Squall()
            >>>
            >>> class BackEndException(Exception): pass
            >>>
            >>> @app.exception_handler(BackEndException)
            >>> async def handle_backend_exception():
            >>>     return JSONResponse(
            >>>         status_code=500,
            >>>         content={"message": "BackEnd error"}
            >>>     )
            >>>
        """

        def decorator(func: typing.Callable[..., Any]) -> typing.Callable[..., Any]:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def add_middleware(self, middleware_class: type, **options: typing.Any) -> None:
        """Adds middleware.

        Examples:
            >>> from squall.middleware.httpsredirect import HTTPSRedirectMiddleware
            >>>
            >>> app = Squall()
            >>>
            >>> app.add_middleware(HTTPSRedirectMiddleware)
        """
        self.user_middleware.insert(0, Middleware(middleware_class, **options))
        self.middleware_stack = self._build_middleware_stack()

    def middleware(self, middleware_type: str) -> typing.Callable[..., Any]:
        """Decorator for middleware registration.

        Examples:
            >>> app = Squall()
            >>>
            >>> @app.middleware("http")
            >>> async def add_process_time_header(request: Request, call_next):
            >>>     start_time = time.time()
            >>>     response = await call_next(request)
            >>>     process_time = time.time() - start_time
            >>>     response.headers["X-Process-Time"] = str(process_time)
            >>>     return response
        """
        assert (
            middleware_type == "http"
        ), 'Currently only middleware("http") is supported.'

        def decorator(func: ASGIApp) -> ASGIApp:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func

        return decorator

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI calls entrypoint."""
        if self.root_path:
            scope["root_path"] = self.root_path
        scope["app"] = self

        if scope["type"] == "lifespan":
            await lifespan(self.lifespan_ctx, scope, receive, send)
            return

        try:
            await self.middleware_stack(scope, receive, send)
        except Exception as exc:
            handler = None

            if isinstance(exc, HTTPException):
                handler = self.exception_handlers.get(exc.status_code)

            if handler is None:
                handler = self._lookup_exception_handler(exc)

            request = Request(scope)
            if handler:
                if iscoroutinefunction(handler):
                    response = await handler(request, exc)
                else:
                    response = await run_in_threadpool(handler, request, exc)
            elif self.debug:
                # In debug mode, return traceback responses.
                response = get_default_debug_response(request, exc)
            else:
                # Use our default 500 error handler.
                response = self._default_error_response

            await send(response.send_start)
            await send(response.send_body)

            if not handler:
                raise exc

    def _lookup_exception_handler(self, exc: Exception) -> typing.Optional[typing.Callable]:
        exception_class = type(exc)
        try:
            return self.exception_handlers[exception_class]
        except KeyError:
            for cls in type(exc).__mro__:
                if cls in self.exception_handlers:
                    self.exception_handlers[exception_class] = self.exception_handlers[cls]
                    return self.exception_handlers[cls]

    def _build_middleware_stack(self) -> ASGIApp:
        """Build stack for middlewares pipelining"""
        app = self.router
        for cls, options in reversed(self.user_middleware):
            app = cls(app=app, **options)
        return app

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

    def _setup(self) -> None:
        """Setups OpenAPI functionality"""
        # return
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
                    self.openapi() #.dict(exclude_unset=True, by_alias=True)  # type: ignore
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
