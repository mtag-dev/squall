import typing
from typing import Any, Awaitable, Callable, Coroutine, MutableMapping, TypeVar

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]

Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., typing.Any])

AnyFunc = Callable[..., Coroutine[Any, Any, Any]]
