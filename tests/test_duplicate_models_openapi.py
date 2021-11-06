from pydantic import Field, dataclasses
from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclasses.dataclass
class Model:
    pass


@dataclasses.dataclass
class Model2:
    a: Model = Field(...)


@dataclasses.dataclass
class Model3:
    c: Model = Field(...)
    d: Model2 = Field(...)


@app.get("/", response_model=Model3)
def f():
    return {"c": {}, "d": {"a": {}}}


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
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
    "components": {
        "schemas": {
            "Model": {"title": "Model", "type": "object", "properties": {}},
            "Model2": {
                "title": "Model2",
                "required": ["a"],
                "type": "object",
                "properties": {"a": {"$ref": "#/components/schemas/Model"}},
            },
            "Model3": {
                "title": "Model3",
                "required": ["c", "d"],
                "type": "object",
                "properties": {
                    "c": {"$ref": "#/components/schemas/Model"},
                    "d": {"$ref": "#/components/schemas/Model2"},
                },
            },
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
