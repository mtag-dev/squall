import inspect
import json
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from apischema.json_schema import (
    JsonSchemaVersion,
    definitions_schema,
    deserialization_schema,
    serialization_schema,
)

normalized = lambda a: json.loads(json.dumps(a))

from squall import routing
from squall.datastructures import DefaultPlaceholder
from squall.openapi.constants import (
    METHODS_WITH_BODY,
    REF_PREFIX,
    STATUS_CODES_WITH_NO_BODY,
)
from squall.openapi.models import OpenAPI
from squall.params import Body
from squall.responses import JSONResponse, PrettyJSONResponse, Response
from squall.utils import generate_operation_id_for_path
from starlette.routing import BaseRoute

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


def get_head_params(route):
    parameters: List[Dict[str, Any]] = []
    for param in route.head_params:
        parameters.append(param.spec)
    return parameters


class OpenAPIRoute:
    def __init__(self, route: routing.APIRoute):
        self.route = route
        self._response_class = route.response_class
        self.request_schemas = set()
        self.response_schemas = set()

    @property
    def response_class(self):
        if isinstance(self._response_class, DefaultPlaceholder):
            current_response_class: Type[Response] = self._response_class.value
        else:
            current_response_class = self._response_class
        return current_response_class

    @property
    def default_status_code(self):
        code = 200
        if self.route.status_code is not None:
            code = str(self.route.status_code)
        else:
            response_signature = inspect.signature(self.response_class.__init__)
            status_code_param = response_signature.parameters.get("status_code")
            if status_code_param is not None:
                if isinstance(status_code_param.default, int):
                    code = str(status_code_param.default)

        return code or 200

    @property
    def responses(self):
        responses = {}
        # Default response
        status_code = self.default_status_code
        responses[status_code] = {"description": self.route.response_description}
        if (
            self.response_class.media_type
            and status_code not in STATUS_CODES_WITH_NO_BODY
        ):
            response_schema = {"type": "string"}
            if self.response_class in (JSONResponse, PrettyJSONResponse):
                if self.route.response_model:
                    response_schema = normalized(
                        deserialization_schema(
                            self.route.response_model,
                            all_refs=True,
                            version=JsonSchemaVersion.OPEN_API_3_1,
                        )
                    )
                    self.response_schemas.add(self.route.response_model)
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
                response_schema = normalized(
                    deserialization_schema(
                        model, all_refs=True, version=JsonSchemaVersion.OPEN_API_3_1
                    )
                )
                self.response_schemas.add(self.route.response_model)
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
        if not self.route.request_model:
            return None

        self.request_schemas.add(self.route.request_model["model"])
        response_schema = normalized(
            serialization_schema(
                self.route.request_model["model"],
                all_refs=True,
                version=JsonSchemaVersion.OPEN_API_3_1,
            )
        )

        field: Optional[Body] = self.route.request_model.get("field")

        media_type = getattr(field, "media_type", "application/json")
        result = dict()
        result["required"] = getattr(field, "required", True)
        content = {media_type: {}}

        if field:
            if field.examples:
                content[media_type]["examples"] = field.examples
            elif field.example:
                content[media_type]["example"] = field.example

        content[media_type]["schema"] = response_schema
        result["content"] = content
        return result

    @property
    def spec(self) -> Dict[str, Any]:
        # Check before calling the function for if route.include_in_schema
        data = {}

        for method in self.route.methods:
            operation = get_openapi_operation_metadata(route=self.route, method=method)
            if parameters := get_head_params(route=self.route):
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
    routes: Sequence[BaseRoute],
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

    request_schemas = set()
    response_schemas = set()
    for route in routes:
        if not route.include_in_schema or not route.path_format:
            continue

        openapi_route = OpenAPIRoute(route)
        paths[route.path_format] = openapi_route.spec
        response_schemas.update(openapi_route.response_schemas)
        request_schemas.update(openapi_route.request_schemas)

    schemas = set.union(request_schemas, response_schemas)
    if schemas:
        components["schemas"] = normalized(
            definitions_schema(
                deserialization=list(schemas),
                all_refs=True,
                version=JsonSchemaVersion.OPEN_API_3_0,
            )
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
    return OpenAPI(**output)  # type: ignore
