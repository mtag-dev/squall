from dataclasses import dataclass
from typing import List, Optional

from apischema import validator
from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class Item:
    age: float
    name: Optional[str] = None

    @validator
    def age_positive(self):
        if self.age <= 0:
            raise ValueError("Age should be greater than 0")


@app.post("/items/")
def save_item_no_body(item: List[Item]):
    return {"item": item}


client = TestClient(app)


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "properties": {
                    "age": {"type": "number"},
                    "name": {"type": ["string", "null"], "default": None},
                },
                "required": ["age"],
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
        "/items/": {
            "post": {
                "summary": "Save Item No Body",
                "operationId": "save_item_no_body_items__post",
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
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Item"},
                            }
                        }
                    },
                },
            }
        }
    },
}

single_error = {"details": [{"loc": [0], "msg": "Age should be greater than 0"}]}

multiple_errors = {
    "details": [
        {"loc": [0, "age"], "msg": "expected type number, found string"},
        {"loc": [1, "age"], "msg": "expected type number, found string"},
    ]
}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_put_correct_body():
    response = client.post("/items/", json=[{"name": "Foo", "age": 5}])
    assert response.status_code == 200, response.text
    assert response.json() == {"item": [{"name": "Foo", "age": 5}]}


def test_validation_error():
    response = client.post("/items/", json=[{"name": "Foo", "age": -1.0}])
    assert response.status_code == 422, response.text
    assert response.json() == single_error


def test_put_incorrect_body_multiple():
    response = client.post("/items/", json=[{"age": "five"}, {"age": "six"}])
    assert response.status_code == 422, response.text
    assert response.json() == multiple_errors
