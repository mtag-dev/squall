import inspect
import typing
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from apischema.json_schema import (
    JsonSchemaVersion,
    definitions_schema,
    deserialization_schema,
    serialization_schema,
)
from squall import routing
from squall.datastructures import DefaultPlaceholder
from squall.openapi.constants import (
    METHODS_WITH_BODY,
    REF_PREFIX,
    STATUS_CODES_WITH_NO_BODY,
)
from squall.params import Body
from squall.responses import JSONResponse, PrettyJSONResponse, Response
from squall.routing import APIRoute, APIWebSocketRoute
from squall.routing_.utils import HeadParam
from squall.utils import generate_operation_id_for_path

AnyRoute = Union[APIRoute, APIWebSocketRoute]


validation_error_definition = {
    "title": "ValidationError",
    "type": "object",
    "properties": {
        "loc": {"title": "Location", "type": "array", "items": {"type": "string"}},
        "msg": {"title": "Message", "type": "string"},
        "type": {"title": "Error Type", "type": "string"},
    },
    "required": ["loc", "msg", "type"],
}

validation_error_response_definition = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Detail",
            "type": "array",
            "items": {"$ref": REF_PREFIX + "ValidationError"},
        }
    },
}


param_validation_error_response_definition = {
    "title": "HTTPBadRequestError",
    "type": "object",
    "properties": {
        "details": {
            "title": "Detail",
            "type": "array",
            "items": {"$ref": REF_PREFIX + "ValidationError"},
        }
    },
}

status_code_ranges: Dict[str, str] = {
    "1XX": "Information",
    "2XX": "Success",
    "3XX": "Redirection",
    "4XX": "Client Error",
    "5XX": "Server Error",
    "DEFAULT": "Default Response",
}


type_mapping: Dict[str, str] = {
    "int": "integer",
    "Decimal": "number",
    "float": "number",
    "bool": "boolean",
    "str": "string",
    "bytes": "string",
}


def generate_operation_id(*, route: routing.APIRoute, method: str) -> str:
    if route.operation_id:
        return route.operation_id
    path: str = route.path_format
    return generate_operation_id_for_path(name=route.name, path=path, method=method)


def generate_operation_summary(*, route: routing.APIRoute, method: str) -> str:
    if route.summary:
        return route.summary
    return route.name.replace("_", " ").title()


def get_openapi_operation_metadata(
    *, route: routing.APIRoute, method: str
) -> Dict[str, Any]:
    operation: Dict[str, Any] = {}
    if route.tags:
        operation["tags"] = route.tags
    operation["summary"] = generate_operation_summary(route=route, method=method)
    if route.description:
        operation["description"] = route.description
    operation["operationId"] = generate_operation_id(route=route, method=method)
    if route.deprecated:
        operation["deprecated"] = route.deprecated
    return operation


class OpenAPIRoute:
    def __init__(self, route: APIRoute, version: JsonSchemaVersion) -> None:
        self.version = version
        self.route = route
        self._response_class = route.response_class
        self.request_schemas: typing.Set[Any] = set()
        self.response_schemas: typing.Set[Any] = set()

    @property
    def response_class(self) -> Type[Response]:
        if isinstance(self._response_class, DefaultPlaceholder):
            current_response_class: Type[Response] = self._response_class.value
        else:
            current_response_class = self._response_class
        return current_response_class

    @property
    def default_status_code(self) -> str:
        code = str(200)
        if self.route.status_code is not None:
            code = str(self.route.status_code)
        else:
            response_signature = inspect.signature(self.response_class.__init__)
            status_code_param = response_signature.parameters.get("status_code")
            if status_code_param is not None:
                code = str(status_code_param.default)

        return code

    @property
    def responses(self) -> Dict[Union[str, int], Any]:
        responses: Dict[Union[int, str], Any] = {}
        # Default response
        status_code: Union[str, int] = self.default_status_code
        responses[status_code] = {"description": self.route.response_description}
        if (
            self.response_class.media_type
            and status_code not in STATUS_CODES_WITH_NO_BODY
        ):
            response_schema = {"type": "string"}
            if self.response_class in (JSONResponse, PrettyJSONResponse):
                if self.route.response_field:
                    response_schema = deserialization_schema(
                        self.route.response_field.model,
                        all_refs=True,
                        version=self.version,
                    )
                    self.response_schemas.add(self.route.response_field.model)
                else:
                    response_schema = {}
            responses[status_code]["content"] = {
                self.response_class.media_type: {"schema": response_schema}
            }

        # Errors
        if self.route.head_params:
            responses["400"] = {
                "description": "Parameters Validation Error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": REF_PREFIX + "HTTPBadRequestError"}
                    }
                },
            }
        # For request_field
        # responses["422"] = {
        #     "description": "Request Body Validation Error",
        #     "content": {
        #         "application/json": {
        #             "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
        #         }
        #     },
        # }

        # User defined responses
        for status_code, response in self.route.responses.items():
            status_code = str(status_code)
            if status_code not in responses:
                responses[status_code] = {}

            if model := response.get("model"):
                response_schema = deserialization_schema(
                    model, all_refs=True, version=self.version
                )
                responses[status_code]["content"] = {
                    self.response_class.media_type: {"schema": response_schema}
                }
            if description := response.get("description"):
                responses[status_code]["description"] = description

            if content := response.get("content"):
                if "content" not in responses[status_code]:
                    responses[status_code]["content"] = content.copy()
                else:
                    responses[status_code]["content"].update(content)

        return responses

    @property
    def request_body(self) -> Optional[Dict[str, Any]]:
        if not self.route.request_field:
            return None

        self.request_schemas.add(self.route.request_field.model)
        response_schema = serialization_schema(
            self.route.request_field.model,
            all_refs=True,
            version=self.version,
        )

        settings: Optional[Body] = self.route.request_field.settings

        media_type = getattr(settings, "media_type", "application/json")
        result = {"required": getattr(settings, "required", True)}
        content: Dict[str, Dict[str, Any]] = {media_type: {}}

        if settings:
            if settings.examples:
                content[media_type]["examples"] = settings.examples
            elif settings.example:
                content[media_type]["example"] = settings.example

        content[media_type]["schema"] = response_schema
        result["content"] = content
        return result

    @staticmethod
    def get_param_spec(param: HeadParam) -> Dict[str, Any]:
        source_mapping = {
            "path_params": "path",
            "query_params": "query",
            "headers": "header",
            "cookies": "cookie",
        }

        item: Dict[str, Any] = {}
        item["type"] = type_mapping.get(param.convertor, "string")

        schema: Dict[str, Any]
        if param.is_array:
            schema = {"type": "array", "items": item}
        else:
            schema = item
            if param.statements.get("ge") is not None:
                schema["minimum"] = param.statements["ge"]
                schema["exclusiveMinimum"] = False
            elif param.statements.get("gt") is not None:
                schema["minimum"] = param.statements["gt"]
                schema["exclusiveMinimum"] = True

            if param.statements.get("le") is not None:
                schema["maximum"] = param.statements["le"]
                schema["exclusiveMaximum"] = False
            elif param.statements.get("lt") is not None:
                schema["maximum"] = param.statements["lt"]
                schema["exclusiveMaximum"] = True

        result = {
            "required": param.default == Ellipsis,
            "schema": schema,
            "name": param.alias or param.name,
            "in": source_mapping[param.source],
        }

        description = getattr(param._default, "description", None)
        if description is not None:
            result["description"] = description

        example = getattr(param._default, "example", None)
        if example is not None:
            result["example"] = example

        examples = getattr(param._default, "examples", None)
        if examples:
            result["examples"] = examples

        deprecated = getattr(param._default, "deprecated", None)
        if deprecated:
            result["deprecated"] = True

        return result

    @property
    def head_params(self) -> List[Dict[str, Any]]:
        parameters: List[Dict[str, Any]] = []
        for param in self.route.head_params:
            parameters.append(self.get_param_spec(param))
        return parameters

    @property
    def spec(self) -> Dict[str, Any]:
        # Check before calling the function for if route.include_in_schema
        data = {}

        for method in self.route.methods:
            operation = get_openapi_operation_metadata(route=self.route, method=method)
            if parameters := self.head_params:
                operation["parameters"] = parameters
            operation["responses"] = self.responses

            if method in METHODS_WITH_BODY:
                if request_body := self.request_body:
                    operation["requestBody"] = request_body

            data[method.lower()] = operation

        return data


def get_openapi(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.0.2",
    description: Optional[str] = None,
    routes: Sequence[AnyRoute],
    tags: Optional[List[Dict[str, Any]]] = None,
    servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
    terms_of_service: Optional[str] = None,
    contact: Optional[Dict[str, Union[str, Any]]] = None,
    license_info: Optional[Dict[str, Union[str, Any]]] = None,
) -> Dict[str, Any]:
    info: Dict[str, Any] = {"title": title, "version": version}
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info
    output: Dict[str, Any] = {"openapi": openapi_version, "info": info}
    if servers:
        output["servers"] = servers
    components: Dict[str, Dict[str, Any]] = {}
    paths: Dict[str, Dict[str, Any]] = {}

    _version = JsonSchemaVersion.OPEN_API_3_1
    request_schemas = set()
    response_schemas = set()
    for route in routes:
        if not route.include_in_schema or not route.path_format:
            continue

        openapi_route = OpenAPIRoute(route, version=_version)
        paths[route.path_format] = openapi_route.spec
        response_schemas.update(openapi_route.response_schemas)
        request_schemas.update(openapi_route.request_schemas)

    schemas = set.union(request_schemas, response_schemas)
    if schemas:
        components["schemas"] = definitions_schema(
            deserialization=list(schemas),
            all_refs=True,
            version=_version,
        )

        # Should be removed from here. Schema should be defined via handlers
        if "ValidationError" not in components["schemas"]:
            components["schemas"]["ValidationError"] = validation_error_definition
        if "HTTPValidationError" not in components["schemas"]:
            components["schemas"][
                "HTTPValidationError"
            ] = validation_error_response_definition
        if "HTTPBadRequestError" not in components["schemas"]:
            components["schemas"][
                "HTTPBadRequestError"
            ] = param_validation_error_response_definition

    if components:
        output["components"] = components
    output["paths"] = paths
    if tags:
        output["tags"] = tags
    return output
