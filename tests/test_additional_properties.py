from dataclasses import dataclass
from typing import Dict

from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class Items:
    items: Dict[str, int]


@app.post("/foo")
def foo(items: Items):
    return items.items


client = TestClient(app)


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Items": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    }
                },
                "required": ["items"],
                "additionalProperties": False,
            },
            "ValidationError": {
                "title": "ValidationError",
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "msg": {"title": "Message", "type": "string"},
                    "type": {"title": "Error Type", "type": "string"},
                },
                "required": ["loc", "msg", "type"],
            },
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Detail",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
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
        "/foo": {
            "post": {
                "summary": "Foo",
                "operationId": "foo_foo_post",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "422": {
                        "description": "Request Body Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Items"}
                        }
                    },
                },
            }
        }
    },
}


def test_additional_properties_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_additional_properties_post():
    response = client.post("/foo", json={"items": {"foo": 1, "bar": 2}})
    assert response.status_code == 200, response.text
    assert response.json() == {"foo": 1, "bar": 2}
