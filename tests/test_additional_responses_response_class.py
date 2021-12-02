import typing
from dataclasses import dataclass

from squall import Squall
from squall.responses import JSONResponse
from squall.testclient import TestClient

app = Squall()


class JsonApiResponse(JSONResponse):
    media_type = "application/vnd.api+json"


@dataclass
class Error:
    status: str
    title: str


@dataclass
class JsonApiError:
    errors: typing.List[Error]


@app.get(
    "/a",
    response_class=JsonApiResponse,
    responses={500: {"description": "Error", "model": JsonApiError}},
)
async def a():
    pass  # pragma: no cover


@app.get("/b", responses={500: {"description": "Error", "model": Error}})
async def b():
    pass  # pragma: no cover


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["status", "title"],
                "additionalProperties": False,
            },
            "JsonApiError": {
                "type": "object",
                "properties": {
                    "errors": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Error"},
                    }
                },
                "required": ["errors"],
                "additionalProperties": False,
            },
            "HTTPBadRequestError": {
                "title": "HTTPBadRequestError",
                "type": "object",
                "properties": {
                    "details": {
                        "title": "Detail",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
            },
        }
    },
    "paths": {
        "/a": {
            "get": {
                "summary": "A",
                "operationId": "a_a_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/vnd.api+json": {"schema": {}}},
                    },
                    "500": {
                        "content": {
                            "application/vnd.api+json": {
                                "schema": {"$ref": "#/components/schemas/JsonApiError"}
                            }
                        },
                        "description": "Error",
                    },
                },
            }
        },
        "/b": {
            "get": {
                "summary": "B",
                "operationId": "b_b_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "500": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                        "description": "Error",
                    },
                },
            }
        },
    },
}


client = TestClient(app)


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema
