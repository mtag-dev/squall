import asyncio
import contextlib
import functools
import traceback
import types
import typing

from squall.types import Receive, Scope, Send

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


class Lifespan:
    def __init__(
        self,
        on_startup: typing.List[typing.Union[typing.Callable, typing.Coroutine]],
        on_shutdown: typing.List[typing.Union[typing.Callable, typing.Coroutine]],
    ):
        self._on_startup = on_startup
        self._on_shutdown = on_shutdown

    @staticmethod
    async def _run_handlers(handlers):
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def __aenter__(self) -> None:
        await self._run_handlers(self._on_startup)

    async def __aexit__(self, *exc_info: object) -> None:
        await self._run_handlers(self._on_shutdown)

    def __call__(self: _T, app: object) -> _T:
        return self


async def lifespan(
    on_startup: typing.List[typing.Union[typing.Callable, typing.Coroutine]],
    on_shutdown: typing.List[typing.Union[typing.Callable, typing.Coroutine]],
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """
    Handle ASGI lifespan messages, which allows us to manage application
    startup and shutdown events.
    """
    started = False
    scope.get("app")
    await receive()
    try:
        async with Lifespan(on_startup, on_shutdown):
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
