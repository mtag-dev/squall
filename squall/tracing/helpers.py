import functools
from typing import Any, Callable, Dict, Optional

from squall.types import Receive, Scope, Send

tracer = None


class CurrentSpan:
    """
    Wraps open telemetry start_as_current_span method.
    Intention to have this class is supporting of feature flag to does nothing
    if open telemetry is disabled on application level and package is not installed.

    """

    def __init__(
        self, span_name: str, enabled: bool, attributes: Optional[Dict[str, str]] = None
    ):
        global tracer
        self.span_name = span_name
        self.enabled = enabled
        if enabled and not tracer:
            try:
                from opentelemetry import trace  # type: ignore

                tracer = trace.get_tracer(__name__)
            except ImportError:
                raise AssertionError(
                    "trace_internals requires OpenTelemtry installed. "
                    "Please read more here: https://github.com/mtag-dev/squall/#opentelemetry-usage"
                )

        self.attributes = attributes

    def __enter__(self) -> None:
        if not self.enabled or tracer is None:
            return

        self.trace = tracer.start_as_current_span(
            self.span_name, attributes=self.attributes
        )
        self.trace.__enter__()

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        if not self.enabled:
            return
        self.trace.__exit__(exc_type, exc_val, exc_tb)


def trace_requests(call_method: Callable) -> Callable:  # type:ignore
    @functools.wraps(call_method)
    async def call(self: Any, scope: Scope, send: Send, receive: Receive) -> None:
        with CurrentSpan(
            scope.get("path", "/"),
            self.trace_internals,
            attributes={
                "http.method": scope.get("method", ""),
                "http.target": scope.get("path", ""),
            },
        ):
            await call_method(self, scope, send, receive)

    return call
