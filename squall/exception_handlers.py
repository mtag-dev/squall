from squall.exceptions import RequestHeadValidationError, RequestPayloadValidationError
from squall.requests import Request
from squall.responses import JSONResponse, PrettyJSONResponse
from starlette.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"details": exc.detail}, status_code=exc.status_code, headers=headers
        )
    else:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


async def request_payload_validation_exception_handler(
    request: Request, exc: RequestPayloadValidationError
) -> PrettyJSONResponse:
    return PrettyJSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"details": exc.errors()},
    )


async def request_head_validation_exception_handler(
    request: Request, exc: RequestHeadValidationError
) -> PrettyJSONResponse:
    return PrettyJSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"details": exc.errors},
    )
