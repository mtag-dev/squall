import decimal
from typing import Any

import orjson
from pydantic import BaseModel
from starlette.responses import FileResponse as FileResponse  # noqa
from starlette.responses import HTMLResponse as HTMLResponse  # noqa
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa
from starlette.responses import RedirectResponse as RedirectResponse  # noqa
from starlette.responses import Response as Response  # noqa
from starlette.responses import StreamingResponse as StreamingResponse  # noqa


def default(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return dict(obj)
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, set):
        return tuple(obj)
    raise TypeError


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> Any:
        return orjson.dumps(content, default=default, option=orjson.OPT_NON_STR_KEYS)
