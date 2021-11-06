import traceback
import typing
import types
import contextlib
import functools

from squall.types import ASGIApp, Receive, Scope, Send, LifeSpanContext

_T = typing.TypeVar("_T")


class _AsyncLiftContextManager(typing.AsyncContextManager[_T]):
    def __init__(self, cm: typing.ContextManager[_T]):
        self._cm = cm

    async def __aenter__(self) -> _T:
        return self._cm.__enter__()

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        return self._cm.__exit__(exc_type, exc_value, traceback)


def _wrap_gen_lifespan_context(
    lifespan_context: typing.Callable[[typing.Any], typing.Generator]
) -> typing.Callable[[typing.Any], typing.AsyncContextManager]:
    cmgr = contextlib.contextmanager(lifespan_context)

    @functools.wraps(cmgr)
    def wrapper(app: typing.Any) -> _AsyncLiftContextManager:
        return _AsyncLiftContextManager(cmgr(app))

    return wrapper


class RouterLifespan:
    def __init__(self, router: "Router"):
        self._router = router

    async def __aenter__(self) -> None:
        pass
#        self._router.startup()

    async def __aexit__(self, *exc_info: object) -> None:
        pass
#        self._router.shutdown()

    def __call__(self: _T, app: object) -> _T:
        return self


async def lifespan(
        scope: Scope,
        receive: Receive,
        send: Send,
) -> None:
    """
    Handle ASGI lifespan messages, which allows us to manage application
    startup and shutdown events.
    """
    started = False
    app = scope.get("app")
    await receive()
    try:
        # async with context(app):
        await send({"type": "lifespan.startup.complete"})
        started = True
        await receive()
    except BaseException:
        exc_text = traceback.format_exc()
        if started:
            await send({"type": "lifespan.shutdown.failed", "message": exc_text})
        else:
            await send({"type": "lifespan.startup.failed", "message": exc_text})
        raise
    else:
        await send({"type": "lifespan.shutdown.complete"})
