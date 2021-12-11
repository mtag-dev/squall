import decimal
import typing
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import orjson
from squall.compression import Compression
from squall.requests import Request
from squall.types import Receive, Scope, Send
from starlette.datastructures import URL, MutableHeaders
from starlette.responses import FileResponse as StarletteFileResponse  # noqa
from starlette.responses import Response as StarletteResponse  # noqa
from starlette.responses import StreamingResponse as StarletteStreamingResponse  # noqa

json_dumps = orjson.dumps
json_option = orjson.OPT_NON_STR_KEYS
json_pretty_option = orjson.OPT_NON_STR_KEYS | orjson.OPT_INDENT_2


def default(obj: Any) -> Any:
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, set):
        return tuple(obj)
    elif isinstance(obj, bytes):
        return obj.decode("utf-8")
    raise TypeError


def init_headers(
    body: bytes,
    charset: str,
    media_type: Optional[str] = None,
    headers: Optional[typing.Mapping[str, str]] = None,
) -> List[Tuple[bytes, bytes]]:
    if headers is None:
        raw_headers: typing.List[typing.Tuple[bytes, bytes]] = []
        populate_content_length = True
        populate_content_type = True
    else:
        raw_headers = [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in headers.items()
        ]
        keys = [h[0] for h in raw_headers]
        populate_content_length = b"content-length" not in keys
        populate_content_type = b"content-type" not in keys

    append = raw_headers.append
    if body and populate_content_length:
        append((b"content-length", str(len(body)).encode()))

    if media_type is not None and populate_content_type:
        content_type = media_type
        if media_type[:5] == "text/":
            content_type += "; charset=" + charset
        append((b"content-type", content_type.encode()))
    return raw_headers


class Response(StarletteResponse):
    media_type = None
    charset: str = "utf-8"
    request: Request

    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.body = body = self.render(content)
        self.raw_headers = raw_headers = init_headers(
            body, self.charset, self.media_type, headers
        )
        self.send_start: Dict[str, Any] = {
            "type": "http.response.start",
            "status": status_code,
            "headers": raw_headers,
        }
        self.send_body = {"type": "http.response.body", "body": body}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        compression: Optional[Compression] = scope["app"].compression
        send_body: Dict[str, Any] = self.send_body

        if (
            scope["type"] == "http"
            and compression
            and len(send_body["body"]) > compression.minimum_size
        ):
            accept_encoding = self.request.headers.get("Accept-Encoding", "")
            for backend in compression.backends:
                if backend.encoding_name in accept_encoding:
                    body = backend.compress(send_body["body"], compression.level)
                    headers = MutableHeaders(raw=self.send_start["headers"])
                    headers["Content-Encoding"] = backend.encoding_name
                    headers["Content-Length"] = str(len(body))
                    headers.add_vary_header("Accept-Encoding")
                    send_body["body"] = body
                    break

        await send(self.send_start)
        await send(send_body)


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> Any:
        return json_dumps(content, default=default, option=json_option)


class PrettyJSONResponse(JSONResponse):
    def render(self, content: Any) -> Any:
        return json_dumps(content, default=default, option=json_pretty_option)


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"


class RedirectResponse(Response):
    def __init__(
        self,
        url: typing.Union[str, URL],
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(
            content=b"",
            status_code=status_code,
            headers=headers,
        )
        self.headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")


class FileResponse(StarletteFileResponse, Response):
    ...


class StreamingResponse(StarletteStreamingResponse, Response):
    ...
