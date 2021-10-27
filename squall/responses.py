from typing import Any

import orjson
from starlette.responses import FileResponse as FileResponse  # noqa
from starlette.responses import HTMLResponse as HTMLResponse  # noqa
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa
from starlette.responses import RedirectResponse as RedirectResponse  # noqa
from starlette.responses import Response as Response  # noqa
from starlette.responses import StreamingResponse as StreamingResponse  # noqa

try:
    import ujson
except ImportError:  # pragma: nocover
    ujson = None  # type: ignore


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


class UJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        assert ujson is not None, "ujson must be installed to use UJSONResponse"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")
