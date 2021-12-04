from typing import Any, Dict, Optional, Sequence, Tuple

from apischema.validation.errors import ValidationError
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


class SquallError(RuntimeError):
    """A generic, Squall-specific error."""


class RequestPayloadValidationError(ValidationError):
    """APISchema validation error for requests"""


class ResponsePayloadValidationError(ValidationError):
    """APISchema validation error for requests"""


class WebSocketRequestValidationError(ValidationError):
    """WebSocket validation error for requests"""


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
