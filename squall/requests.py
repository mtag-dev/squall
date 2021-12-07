import typing
from collections.abc import Mapping
from http import cookies as http_cookies
from typing import Any, Dict, Optional

import anyio
import orjson
from starlette.datastructures import URL, Address, FormData, Headers, QueryParams, State
from starlette.formparsers import FormParser, MultiPartParser
from starlette.types import Message, Receive, Scope, Send

try:
    from multipart.multipart import parse_options_header  # type: ignore
except ImportError:  # pragma: nocover
    parse_options_header = None


json_loads = orjson.loads

SERVER_PUSH_HEADERS_TO_COPY = {
    "accept",
    "accept-encoding",
    "accept-language",
    "cache-control",
    "user-agent",
}


def cookie_parser(cookie_string: str) -> typing.Dict[str, str]:
    """
    This function parses a ``Cookie`` HTTP header into a dict of key/value pairs.

    It attempts to mimic browser cookie parsing behavior: browsers and web servers
    frequently disregard the spec (RFC 6265) when setting and reading cookies,
    so we attempt to suit the common scenarios here.

    This function has been adapted from Django 3.1.0.
    Note: we are explicitly _NOT_ using `SimpleCookie.load` because it is based
    on an outdated spec and will fail on lots of input we want to support
    """
    cookie_dict: typing.Dict[str, str] = {}
    for chunk in cookie_string.split(";"):
        key, val = chunk.split("=", 1) if "=" in chunk else ("", chunk)
        key, val = key.strip(), val.strip()
        if key or val:
            # unquote using Python's algorithm.
            cookie_dict[key] = http_cookies._unquote(val)
    return cookie_dict


class ClientDisconnect(Exception):
    pass


class HTTPConnection(Mapping[str, Any]):
    """
    A base class for incoming HTTP connections, that is used to provide
    any functionality that is common to both `Request` and `WebSocket`.
    """

    def __init__(self, scope: Scope) -> None:
        assert scope["type"] in ("http", "websocket")
        self.scope = scope
        self.path_params = scope.get("path_params", {})

    def __getitem__(self, key: str) -> typing.Any:
        return self.scope[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)

    # Don't use the `abc.Mapping.__eq__` implementation.
    # Connection instances should never be considered equal
    # unless `self is other`.
    __eq__ = object.__eq__
    __hash__ = object.__hash__

    @property
    def app(self) -> typing.Any:
        return self.scope["app"]

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            self._url = URL(scope=self.scope)
        return self._url

    @property
    def base_url(self) -> URL:
        if not hasattr(self, "_base_url"):
            base_url_scope = dict(self.scope)
            base_url_scope["path"] = "/"
            base_url_scope["query_string"] = b""
            base_url_scope["root_path"] = base_url_scope.get(
                "app_root_path", base_url_scope.get("root_path", "")
            )
            self._base_url = URL(scope=base_url_scope)
        return self._base_url

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):
            self._query_params = QueryParams(self.scope["query_string"])
        return self._query_params

    # @property
    # def path_params(self) -> dict:
    #     return self.scope.get("path_params", {})

    @property
    def cookies(self) -> typing.Dict[str, str]:
        if not hasattr(self, "_cookies"):
            cookies: typing.Dict[str, str] = {}
            cookie_header = self.headers.get("cookie")

            if cookie_header:
                cookies = cookie_parser(cookie_header)
            self._cookies = cookies
        return self._cookies

    @property
    def client(self) -> Address:
        host, port = self.scope.get("client") or (None, None)
        return Address(host=host, port=port)

    @property
    def session(self) -> Any:
        assert (
            "session" in self.scope
        ), "SessionMiddleware must be installed to access request.session"
        return self.scope["session"]

    @property
    def auth(self) -> typing.Any:
        assert (
            "auth" in self.scope
        ), "AuthenticationMiddleware must be installed to access request.auth"
        return self.scope["auth"]

    @property
    def user(self) -> typing.Any:
        assert (
            "user" in self.scope
        ), "AuthenticationMiddleware must be installed to access request.user"
        return self.scope["user"]

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            # Ensure 'state' has an empty dict if it's not already populated.
            self.scope.setdefault("state", {})
            # Create a state instance with a reference to the dict in which it should
            # store info
            self._state = State(self.scope["state"])
        return self._state


async def empty_receive() -> Message:
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: Message) -> None:
    raise RuntimeError("Send channel has not been made available")


class Request(HTTPConnection):
    _json: Dict[str, Any]
    _body: bytes

    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False

    @property
    def method(self) -> str:
        method: str = self.scope["method"]
        return method

    @property
    def receive(self) -> Receive:
        return self._receive

    async def stream(self) -> typing.AsyncGenerator[bytes, None]:
        if hasattr(self, "_body"):
            yield self._body
            yield b""
            return

        if self._stream_consumed:
            raise RuntimeError("Stream consumed")

        self._stream_consumed = True
        message_get = dict.get
        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                if body := message_get(message, "body"):
                    yield body
                if not message_get(message, "more_body"):
                    break
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
                raise ClientDisconnect()
        yield b""

    async def body(self) -> bytes:
        cached_body: Optional[bytes] = getattr(self, "_body", None)
        if cached_body is not None:
            return cached_body

        message_get = dict.get

        chunks = []
        message = await self._receive()
        if message["type"] == "http.request":
            body: bytes = message_get(message, "body", b"")
            if not message_get(message, "more_body"):
                self._body = body
                return body
            chunks.append(body)
        elif message["type"] == "http.disconnect":
            self._is_disconnected = True
            raise ClientDisconnect()

        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                if body := message_get(message, "body", b""):
                    chunks.append(body)
                if not message_get(message, "more_body"):
                    self._body = _body = b"".join(chunks)
                    return _body
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
                raise ClientDisconnect()

    async def json(self) -> typing.Any:
        if hasattr(self, "_json"):
            return self._json

        if cached_body := getattr(self, "_body", None) is not None:
            self._json = _json = json_loads(cached_body)  # type: ignore
            return _json

        if self._stream_consumed:
            raise RuntimeError("Stream consumed")

        self._stream_consumed = True

        message_get = dict.get

        chunks = []
        message = await self._receive()
        if message["type"] == "http.request":
            body = message_get(message, "body", b"")
            if not message_get(message, "more_body"):
                self._body = body
                self._json = _json = json_loads(body)
                return _json
            chunks.append(body)
        elif message["type"] == "http.disconnect":
            self._is_disconnected = True
            raise ClientDisconnect()

        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                if body := message_get(message, "body"):
                    chunks.append(body)
                    if not message_get(message, "more_body"):
                        self._body = b"".join(chunks)
                        self._json = _json = json_loads(self._body)
                        return _json
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
                raise ClientDisconnect()

    async def form(self) -> FormData:
        if not hasattr(self, "_form"):
            assert (
                parse_options_header is not None
            ), "The `python-multipart` library must be installed to use form parsing."
            content_type_header = self.headers.get("Content-Type")
            content_type, options = parse_options_header(content_type_header)
            if content_type == b"multipart/form-data":
                multipart_parser = MultiPartParser(self.headers, self.stream())
                self._form = await multipart_parser.parse()
            elif content_type == b"application/x-www-form-urlencoded":
                form_parser = FormParser(self.headers, self.stream())
                self._form = await form_parser.parse()
            else:
                self._form = FormData()
        return self._form

    async def close(self) -> None:
        form = getattr(self, "_form", None)
        if form is not None:
            await form.close()

    async def is_disconnected(self) -> bool:
        if not self._is_disconnected:
            message: Message

            # If message isn't immediately available, move on
            with anyio.CancelScope() as cs:
                cs.cancel()
                message = await self._receive()

            if message.get("type") == "http.disconnect":
                self._is_disconnected = True

        return self._is_disconnected

    async def send_push_promise(self, path: str) -> None:
        if "http.response.push" in self.scope.get("extensions", {}):
            raw_headers = []
            for name in SERVER_PUSH_HEADERS_TO_COPY:
                for value in self.headers.getlist(name):
                    raw_headers.append(
                        (name.encode("latin-1"), value.encode("latin-1"))
                    )
            await self._send(
                {"type": "http.response.push", "path": path, "headers": raw_headers}
            )
