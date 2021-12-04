from dataclasses import dataclass, field

from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class Model:
    pass


@dataclass
class Model2:
    a: Model = field()


@dataclass
class Model3:
    c: Model = field()
    d: Model2 = field()


@app.get("/", response_model=Model3)
def f():
    return {"c": {}, "d": {"a": {}}}


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Model3": {
                "type": "object",
                "properties": {
                    "c": {"$ref": "#/components/schemas/Model"},
                    "d": {"$ref": "#/components/schemas/Model2"},
                },
                "required": ["c", "d"],
                "additionalProperties": False,
            },
            "Model": {"type": "object", "additionalProperties": False},
            "Model2": {
                "type": "object",
                "properties": {"a": {"$ref": "#/components/schemas/Model"}},
                "required": ["a"],
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
        "/": {
            "get": {
                "summary": "F",
                "operationId": "f__get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Model3"}
                            }
                        },
                    }
                },
            }
        }
    },
}


client = TestClient(app)


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_get_api_route():
    response = client.get("/")
    assert response.status_code == 200, response.text
    assert response.json() == {"c": {}, "d": {"a": {}}}
