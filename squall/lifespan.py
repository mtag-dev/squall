import asyncio
import traceback
from typing import List, TypeVar

from squall.types import AnyFunc, Receive, Scope, Send

_T = TypeVar("_T")


class LifespanContext:
    def __init__(self, on_startup: List[AnyFunc], on_shutdown: List[AnyFunc]):
        self._on_startup = on_startup
        self._on_shutdown = on_shutdown

    @staticmethod
    async def _run_handlers(handlers: List[AnyFunc]) -> None:
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
    ctx: LifespanContext,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """
    Handle ASGI lifespan messages, which allows us to manage application
    startup and shutdown events.
    """
    started = False
    await receive()
    try:
        async with ctx:
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
