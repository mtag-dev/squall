from starlette.requests import HTTPConnection as HTTPConnection  # noqa: F401
from starlette.requests import Request as SlRequest  # noqa: F401


class Request(SlRequest):
    ...
