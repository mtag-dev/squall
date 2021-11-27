from html import escape
from traceback import format_exception, TracebackException
from inspect import getinnerframes
from starlette.exceptions import ExceptionMiddleware, HTTPException
from squall.types import Receive
from squall.requests import Request
from squall.responses import Response, HTMLResponse, PlainTextResponse
from starlette.middleware.errors import TEMPLATE, STYLES, JS


def generate_html(self, exc: Exception, limit: int = 7) -> str:
    traceback_obj = TracebackException.from_exception(exc, capture_locals=True)

    exc_html = ""
    is_collapsed = False
    exc_traceback = exc.__traceback__
    if exc_traceback is not None:
        frames = getinnerframes(exc_traceback, limit)
        for frame in reversed(frames):
            exc_html += self.generate_frame_html(frame, is_collapsed)
            is_collapsed = True

    # escape error class and text
    error = (
        f"{escape(traceback_obj.exc_type.__name__)}: "
        f"{escape(str(traceback_obj))}"
    )

    return TEMPLATE.format(styles=STYLES, js=JS, error=error, exc_html=exc_html)


def get_default_debug_response(request: Request, exc: Exception) -> Response:
    accept = request.headers.get("accept", "")

    if "text/html" in accept:
        content = generate_html(exc)
        return HTMLResponse(content, status_code=500)
    content = "".join(format_exception(type(exc), exc, exc.__traceback__))
    return PlainTextResponse(content, status_code=500)


def get_default_error_response(request: Request, exc: Exception) -> Response:
    return PlainTextResponse("Internal Server Error", status_code=500)