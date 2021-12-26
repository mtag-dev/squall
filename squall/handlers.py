import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type, Union

from apischema import ValidationError
from orjson import JSONDecodeError
from squall.bindings import RequestField
from squall.datastructures import Default, DefaultPlaceholder
from squall.exceptions import (
    HTTPException,
    RequestHeadValidationError,
    RequestPayloadValidationError,
    ResponsePayloadValidationError,
    WebSocketRequestValidationError,
)
from squall.requests import Request
from squall.responses import JSONResponse, Response
from squall.types import ASGIApp
from squall.websockets import WebSocket
from starlette.concurrency import run_in_threadpool
from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.types import Receive, Scope, Send


def get_http_handler(
    endpoint: Callable[..., Any],
    head_validator: Optional[Callable[..., Any]] = None,
    body_fields: Optional[List[Any]] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    request_field: Optional[RequestField] = None,
    request_deserializer: Optional[Callable[..., Any]] = None,
    response_deserializer: Optional[Callable[..., Any]] = None,
    response_serializer: Optional[Callable[..., Any]] = None,
) -> ASGIApp:
    is_coroutine = asyncio.iscoroutinefunction(endpoint)
    # is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    request_model = request_model_param = None
    if request_field is not None:
        request_model_param = request_field.name
        request_model = request_field.model

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)

        # Head validation
        if head_validator is not None:
            kwargs, errors = head_validator(request)
            if errors:
                raise RequestHeadValidationError(errors)
        else:
            kwargs = {}

        # Body fields and request object
        form = None
        try:
            if request_model is not None and request_deserializer is not None:
                body = await request.json()
                kwargs[request_model_param] = request_deserializer(body)

            if body_fields:
                form_missed = []
                for field in body_fields:
                    kind = field["kind"]
                    if kind == "request":
                        kwargs[field["name"]] = request
                    elif kind == "body":
                        ct = request.headers.get("content-type")
                        if ct is not None and ct[-4:] == "json":
                            kwargs[field["name"]] = await request.json()
                        else:
                            kwargs[field["name"]] = await request.body()
                    elif kind == "form":
                        if form is None:
                            form = await request.form()
                        value = form.get(field["name"])
                        if value is None:
                            form_missed.append(
                                {
                                    "loc": ["form", field["name"]],
                                    "msg": "field required",
                                }
                            )
                        else:
                            kwargs[field["name"]] = form.get(field["name"])
                if form_missed:
                    raise ValidationError.from_errors(form_missed)  # type: ignore
        except JSONDecodeError as e:
            raise RequestPayloadValidationError([str(e)])
        except ValidationError as e:
            raise RequestPayloadValidationError(e.messages, e.children)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

        if is_coroutine:
            raw_response = await endpoint(**kwargs)
        else:
            raw_response = await run_in_threadpool(endpoint, **kwargs)

        if isinstance(raw_response, Response):
            raw_response.request = request
            await raw_response(scope, receive, send)
            return

        response_args: Dict[str, Any] = {}

        # If status_code was set, use it, otherwise use the default from the
        # response class, in the case of redirect it's 307

        try:
            if response_deserializer is not None and response_serializer is not None:
                result = response_serializer(response_deserializer(raw_response))
            elif response_serializer is not None:
                result = response_serializer(raw_response)
            else:
                result = raw_response
        except ValidationError as e:
            raise ResponsePayloadValidationError(e.messages, e.children)
        except TypeError as e:
            raise ResponsePayloadValidationError([str(e)])

        if status_code is not None:
            response_args["status_code"] = status_code
        response = actual_response_class(result, **response_args)
        # Temporary solution in order to avoid header initialization
        response.request = request
        await response(scope, receive, send)

    return app


def get_websocket_handler(
    endpoint: Callable[..., Any],
    head_validator: Optional[Callable[..., Any]] = None,
) -> Callable[[WebSocket], Coroutine[Any, Any, Any]]:
    async def app(websocket: WebSocket) -> None:
        # Head validation
        if head_validator is not None:
            kwargs, errors = head_validator(websocket)
            if errors:
                await websocket.close(code=WS_1008_POLICY_VIOLATION)
                raise WebSocketRequestValidationError(errors)
        else:
            kwargs = {}
        await endpoint(websocket, **kwargs)

    return app
