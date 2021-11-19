from typing import Any, Dict, Optional, Sequence, Tuple, Type

from pydantic import BaseModel, ValidationError, create_model
from pydantic.error_wrappers import ErrorList
from starlette.exceptions import HTTPException as StarletteHTTPException


class HTTPException(StarletteHTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.headers = headers


RequestErrorModel: Type[BaseModel] = create_model("Request")
WebSocketErrorModel: Type[BaseModel] = create_model("WebSocket")


class SquallError(RuntimeError):
    """
    A generic, Squall-specific error.
    """


class RequestPayloadValidationError(ValidationError):
    def __init__(self, errors: Sequence[ErrorList], *, body: Any = None) -> None:
        self.body = body
        super().__init__(errors, RequestErrorModel)


class RequestHeadValidationError(Exception):
    def __init__(self, errors: Sequence[Tuple[str, str, str, Any]]) -> None:
        self.errors = []
        for source, field, reason, value in errors:
            error = {
                "loc": [source, field],
                "msg": reason,
            }
            if value != Ellipsis:
                error["val"] = value
            self.errors.append(error)


class WebSocketRequestValidationError(ValidationError):
    def __init__(self, errors: Sequence[ErrorList]) -> None:
        super().__init__(errors, WebSocketErrorModel)
