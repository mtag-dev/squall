from html import escape
from inspect import FrameInfo, getinnerframes
from traceback import TracebackException, format_exception

from squall.requests import Request
from squall.responses import HTMLResponse, PlainTextResponse, Response
from starlette.middleware.errors import JS, STYLES, TEMPLATE

FRAME_TEMPLATE = """
<div>
    <p class="frame-title">File <span class="frame-filename">{frame_filename}</span>,
    line <i>{frame_lineno}</i>,
    in <b>{frame_name}</b>
    <span class="collapse-btn" data-frame-id="{frame_filename}-{frame_lineno}" onclick="collapse(this)">{collapse_button}</span>
    </p>
    <div id="{frame_filename}-{frame_lineno}" class="source-code {collapsed}">{code_context}</div>
</div>
"""  # noqa: E501

LINE = """
<p><span class="frame-line">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""

CENTER_LINE = """
<p class="center-line"><span class="frame-line center-line">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""


def format_line(index: int, line: str, frame_lineno: int, frame_index: int) -> str:
    values = {
        # HTML escape - line could contain < or >
        "line": escape(line).replace(" ", "&nbsp"),
        "lineno": (frame_lineno - frame_index) + index,
    }

    if index != frame_index:
        return LINE.format(**values)
    return CENTER_LINE.format(**values)


def generate_frame_html(frame: FrameInfo, is_collapsed: bool) -> str:
    assert frame.index is not None
    code_context = "".join(
        format_line(index, line, frame.lineno, frame.index)
        for index, line in enumerate(frame.code_context or [])
    )

    values = {
        # HTML escape - filename could contain < or >, especially if it's a virtual
        # file e.g. <stdin> in the REPL
        "frame_filename": escape(frame.filename),
        "frame_lineno": frame.lineno,
        # HTML escape - if you try very hard it's possible to name a function with <
        # or >
        "frame_name": escape(frame.function),
        "code_context": code_context,
        "collapsed": "collapsed" if is_collapsed else "",
        "collapse_button": "+" if is_collapsed else "&#8210;",
    }
    return FRAME_TEMPLATE.format(**values)


def generate_html(exc: Exception, limit: int = 7) -> str:
    traceback_obj = TracebackException.from_exception(exc, capture_locals=True)

    exc_html = ""
    is_collapsed = False
    exc_traceback = exc.__traceback__
    if exc_traceback is not None:
        frames = getinnerframes(exc_traceback, limit)
        for frame in reversed(frames):
            exc_html += generate_frame_html(frame, is_collapsed)
            is_collapsed = True

    # escape error class and text
    error = (
        f"{escape(traceback_obj.exc_type.__name__)}: " f"{escape(str(traceback_obj))}"
    )

    return TEMPLATE.format(styles=STYLES, js=JS, error=error, exc_html=exc_html)


def get_default_debug_response(request: Request, exc: Exception) -> Response:
    """Generate default error response if debug enabled"""
    accept = request.headers.get("accept", "")

    if "text/html" in accept:
        content = generate_html(exc)
        return HTMLResponse(content, status_code=500)
    content = "".join(format_exception(type(exc), exc, exc.__traceback__))
    return PlainTextResponse(content, status_code=500)
