import asyncio
import enum
import inspect
import re
from decimal import Decimal
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    Type,
    Union,
)

from orjson import JSONDecodeError
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.fields import ModelField
from squall.datastructures import Default, DefaultPlaceholder
from squall.exceptions import (
    HTTPException,
    RequestHeadValidationError,
    RequestPayloadValidationError,
)
from squall.openapi.constants import STATUS_CODES_WITH_NO_BODY
from squall.requests import Request
from squall.responses import JSONResponse, Response
from squall.routing_.utils import get_handler_body_params, get_handler_head_params
from squall.utils import (
    create_cloned_field,
    create_response_field,
    generate_operation_id_for_path,
)
from squall.validators.head import Validator
from starlette.concurrency import run_in_threadpool
from starlette.routing import BaseRoute as SlBaseRoute
from starlette.routing import Route as SlRoute
from starlette.routing import WebSocketRoute as SlWebSocketRoute
from starlette.routing import get_name, websocket_session
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket


class WebSocketRoute(SlWebSocketRoute):
    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path


class NoMatchFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` and `.url_path_for(name, **path_params)`
    if no matching route exists.
    """


from starlette.convertors import CONVERTOR_TYPES, Convertor

# Match parameters in URL paths, eg. '{param}', and '{param:int}'
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


def compile_path(
    path: str,
) -> Tuple[Pattern, str, Dict[str, Convertor]]:
    """
    Given a path string, like: "/{username:str}", return a three-tuple
    of (regex, format, {param_name:convertor}).
    regex:      "/(?P<username>[^/]+)"
    format:     "/{username}"
    convertors: {"username": StringConvertor()}
    """
    path_regex = "^"
    path_format = ""
    duplicated_params = set()

    idx = 0
    param_convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")
        assert (
            convertor_type in CONVERTOR_TYPES
        ), f"Unknown path convertor '{convertor_type}'"
        convertor = CONVERTOR_TYPES[convertor_type]

        path_regex += re.escape(path[idx : match.start()])
        path_regex += f"(?P<{param_name}>{convertor.regex})"

        path_format += path[idx : match.start()]
        path_format += "{%s}" % param_name

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = convertor

        idx = match.end()

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    path_regex += re.escape(path[idx:]) + "$"
    path_format += path[idx:]

    return re.compile(path_regex), path_format, param_convertors


def get_request_handler(
    endpoint: Callable[..., Any],
    head_validator: Callable[..., Any],
    body_fields: List[Any],
    # body_field: Optional[ModelField] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    dependency_overrides_provider: Optional[Any] = None,
    response_field: Optional[ModelField] = None,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    is_coroutine = asyncio.iscoroutinefunction(endpoint)
    # is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)

        # Head validation
        kwargs, errors = head_validator(request)
        if errors:
            raise RequestHeadValidationError(errors)

        # Body fields and request object
        form = None
        try:
            for field in body_fields:
                kind = field["kind"]
                if kind == "request":
                    kwargs[field["name"]] = request
                elif kind == "model":
                    body = await request.json()
                    kwargs[field["name"]] = field["model_class"](**body)
                elif kind == "body":
                    ct = request.headers.get("content-type")
                    if ct is not None and ct[-4:] == "json":
                        kwargs[field["name"]] = await request.json()
                    else:
                        kwargs[field["name"]] = await request.body()
                elif kind == "form":
                    if form is None:
                        form = await request.form()
                    kwargs[field["name"]] = form.get(field["name"])

        except JSONDecodeError as e:
            raise RequestPayloadValidationError(
                [ErrorWrapper(e, ("body", e.pos))], body=e.doc
            )
        except ValidationError as e:
            raise RequestPayloadValidationError([ErrorWrapper(e, ("body",))])
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

        if is_coroutine:
            raw_response = await endpoint(**kwargs)
        else:
            raw_response = await run_in_threadpool(endpoint, **kwargs)

        if isinstance(raw_response, Response):
            await raw_response(scope, receive, send)
            return
            # return raw_response

        response_args: Dict[str, Any] = {}
        # If status_code was set, use it, otherwise use the default from the
        # response class, in the case of redirect it's 307
        if response_field is not None:
            response_value, response_errors = response_field.validate(
                raw_response, {}, loc=("response",)
            )
            if response_errors:
                raise ValidationError([response_errors], response_field.type_)
        else:
            response_value = raw_response

        if status_code is not None:
            response_args["status_code"] = status_code
        response = actual_response_class(response_value, **response_args)
        await response(scope, receive, send)

        # try:
        #     body: Any = None
        #     if True: # body_field:
        #         if False: # is_body_form:
        #             body = await request.form()
        #         else:
        #             body_bytes = await request.body()
        #             if body_bytes:
        #                 json_body: Any = Undefined
        #                 content_type_value = request.headers.get("content-type")
        #                 if not content_type_value:
        #                     json_body = await request.json()
        #                 else:
        #                     message = email.message.Message()
        #                     message["content-type"] = content_type_value
        #                     if message.get_content_maintype() == "application":
        #                         subtype = message.get_content_subtype()
        #                         if subtype == "json" or subtype.endswith("+json"):
        #                             json_body = await request.json()
        #                 if json_body != Undefined:
        #                     body = json_body
        #                 else:
        #                     body = body_bytes
        # except json.JSONDecodeError as e:
        #     raise RequestPayloadValidationError([ErrorWrapper(e, ("body", e.pos))], body=e.doc)
        # except Exception as e:
        #     raise HTTPException(
        #         status_code=400, detail="There was an error parsing the body"
        #     ) from e

        # # solved_result = await solve_dependencies(
        # #     request=request,
        # #     dependant=dependant,
        # #     body=body,
        # #     dependency_overrides_provider=dependency_overrides_provider,
        # # )
        # values, errors, background_tasks, sub_response, _ = solved_result
        # if errors:
        #     raise RequestPayloadValidationError(errors, body=body)
        # else:
        # if True:
        #     if is_coroutine:
        #         raw_response = await endpoint(**kwargs)
        #     else:
        #         raw_response = await run_in_threadpool(endpoint, **kwargs)
        #
        #     if isinstance(raw_response, Response):
        #         await raw_response(scope, receive, send)
        #         return
        #         # return raw_response
        #
        #     response_args: Dict[str, Any] = {}
        #     # If status_code was set, use it, otherwise use the default from the
        #     # response class, in the case of redirect it's 307
        #     if response_field is not None:
        #         response_value, response_errors = response_field.validate(
        #             raw_response, {}, loc=("response",)
        #         )
        #         if response_errors:
        #             raise ValidationError([response_errors], response_field.type_)
        #     else:
        #         response_value = raw_response
        #
        #     if status_code is not None:
        #         response_args["status_code"] = status_code
        #     response = actual_response_class(response_value, **response_args)
        #     # response.headers.raw.extend(sub_response.headers.raw)
        #     # if sub_response.status_code:
        #     #     response.status_code = sub_response.status_code
        #     await response(scope, receive, send)

    return app


def get_websocket_app(
    # dependant: Dependant,
    # dependency_overrides_provider: Optional[Any] = None
) -> Callable[[WebSocket], Coroutine[Any, Any, Any]]:
    async def app(websocket: WebSocket) -> None:
        pass
        # solved_result = await solve_dependencies(
        #     request=websocket,
        #     dependant=dependant,
        #     dependency_overrides_provider=dependency_overrides_provider,
        # )
        # values, errors, _, _2, _3 = solved_result
        # if errors:
        #     await websocket.close(code=WS_1008_POLICY_VIOLATION)
        #     raise WebSocketRequestValidationError(errors)
        # assert dependant.call is not None, "dependant.call must be a function"
        # await dependant.call(**values)

    return app


def build_head_validator(handler: Callable[..., Any]):
    v = Validator(
        args=["request"],
        convertors={
            "int": int,
            "float": float,
            "Decimal": Decimal,
            "str": str,
            "bytes": lambda a: a.encode("utf-8"),
        },
    )
    for rule in get_handler_head_params(handler):
        v.add_rule(
            attribute=rule["source"],
            name=rule["name"],
            key=rule.get("origin", rule["name"]),
            check=rule.get("validate"),
            convert=rule.get("convert"),
            as_list=rule.get("as_list", False),
            default=rule.get("default", Ellipsis),
            gt=rule.get("gt"),
            ge=rule.get("ge"),
            lt=rule.get("lt"),
            le=rule.get("le"),
            min_length=rule.get("min_length"),
            max_length=rule.get("max_length"),
        )
        print(
            dict(
                source=rule["source"],
                name=rule["name"],
                key=rule.get("origin", rule["name"]),
                check=rule.get("validate"),
                convert=rule.get("convert"),
                default=rule.get("default", "..."),
                as_list=rule.get("as_list", False),
                gt=rule.get("gt"),
                ge=rule.get("ge"),
                lt=rule.get("lt"),
                le=rule.get("le"),
                min_length=rule.get("min_length"),
                max_length=rule.get("max_length"),
            )
        )
    return v.build()


class Route(SlRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        super(Route, self).__init__(
            path,
            endpoint,
            methods=methods,  # type: ignore
            name=name,  # type: ignore
            include_in_schema=include_in_schema,
        )

    def matches(self, scope: Scope) -> Tuple[bool, Scope]:
        _match, endpoint = self.match_hack
        match = _match(scope["path"])
        if match:
            return True, {"endpoint": endpoint, "path_params": match.groupdict()}
        return False, {}


class APIWebSocketRoute(WebSocketRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        name: Optional[str] = None,
        dependency_overrides_provider: Optional[Any] = None,
    ) -> None:
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.name = get_name(endpoint) if name is None else name
        # self.dependant = get_dependant(path=path, call=self.endpoint)
        self.app = websocket_session(
            get_websocket_app(
                dependant=self.dependant,
                dependency_overrides_provider=dependency_overrides_provider,
            )
        )
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)

    def set_defaults(self) -> None:
        self.path = self._path_origin

    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )

    def matches(self, scope: Scope) -> Tuple[bool, Scope]:
        match = self.path_regex.match(scope["path"])
        if match:
            return True, match.groupdict()
        return False, {}


class APIRoute(Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        # dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        name: Optional[str] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        dependency_overrides_provider: Optional[Any] = None,
        callbacks: Optional[List[SlBaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        # normalise enums e.g. http.HTTPStatus
        if isinstance(status_code, enum.IntEnum):
            status_code = int(status_code)
        self.path = self._path_origin = path
        self.endpoint = endpoint
        self.head_validator = build_head_validator(endpoint)
        self.body_fields = get_handler_body_params(endpoint)
        self.name = get_name(endpoint) if name is None else name
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
        if methods is None:
            methods = ["GET"]
        self.methods: Set[str] = {method.upper() for method in methods}
        self.unique_id = generate_operation_id_for_path(
            name=self.name, path=self.path_format, method=list(methods)[0]
        )
        self.response_model = response_model
        if self.response_model:
            assert (
                status_code not in STATUS_CODES_WITH_NO_BODY
            ), f"Status code {status_code} must not have a response body"
            response_name = "Response_" + self.unique_id
            self.response_field = create_response_field(
                name=response_name, type_=self.response_model
            )
            # Create a clone of the field, so that a Pydantic submodel is not returned
            # as is just because it's an instance of a subclass of a more limited class
            # e.g. UserInDB (containing hashed_password) could be a subclass of User
            # that doesn't have the hashed_password. But because it's a subclass, it
            # would pass the validation and be returned as is.
            # By being a new field, no inheritance will be passed as is. A new model
            # will be always created.
            self.secure_cloned_response_field: Optional[
                ModelField
            ] = create_cloned_field(self.response_field)
        else:
            self.response_field = None  # type: ignore
            self.secure_cloned_response_field = None
        self.status_code = status_code
        self.tags = tags or []
        # self.dependencies = list(dependencies) if dependencies else []
        self.summary = summary
        self.description = description or inspect.cleandoc(self.endpoint.__doc__ or "")
        # if a "form feed" character (page break) is found in the description text,
        # truncate description text to the content preceding the first "form feed"
        self.description = self.description.split("\f")[0]
        self.response_description = response_description
        self.responses = responses or {}
        response_fields = {}
        for additional_status_code, response in self.responses.items():
            assert isinstance(response, dict), "An additional response must be a dict"
            model = response.get("model")
            if model:
                assert (
                    additional_status_code not in STATUS_CODES_WITH_NO_BODY
                ), f"Status code {additional_status_code} must not have a response body"
                response_name = f"Response_{additional_status_code}_{self.unique_id}"
                response_field = create_response_field(name=response_name, type_=model)
                response_fields[additional_status_code] = response_field
        if response_fields:
            self.response_fields: Dict[Union[int, str], ModelField] = response_fields
        else:
            self.response_fields = {}
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.include_in_schema = include_in_schema
        self.response_class = response_class

        assert callable(endpoint), "An endpoint must be a callable"

        # self.dependant = get_dependant(path=self.path_format, call=self.endpoint)
        # for depends in self.dependencies[::-1]:
        #     self.dependant.dependencies.insert(
        #         0,
        #         get_parameterless_sub_dependant(depends=depends, path=self.path_format),
        #     )
        # self.body_field = get_body_field(dependant=self.dependant, name=self.unique_id)

        self.dependency_overrides_provider = dependency_overrides_provider
        self.callbacks = callbacks
        self.app = self.get_route_handler()
        self.openapi_extra = openapi_extra

        self.match_hack = (self.path_regex.match, self.endpoint)

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        return get_request_handler(
            endpoint=self.endpoint,
            # dependant=self.dependant,
            # body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class,
            dependency_overrides_provider=self.dependency_overrides_provider,
            response_field=self.response_field,
            head_validator=self.head_validator,
            body_fields=self.body_fields,
        )

    def set_defaults(self) -> None:
        self.path = self._path_origin

    def add_path_prefix(self, prefix: str) -> None:
        self.path = prefix + self.path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
