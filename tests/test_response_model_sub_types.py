from dataclasses import dataclass
from typing import List

from squall import Squall
from squall.testclient import TestClient


@dataclass
class Model:
    name: str


app = Squall()


@app.get("/valid1", responses={"500": {"model": int}})
def valid1():
    pass


@app.get("/valid2", responses={"500": {"model": List[int]}})
def valid2():
    pass


@app.get("/valid3", responses={"500": {"model": Model}})
def valid3():
    pass


@app.get("/valid4", responses={"500": {"model": List[Model]}})
def valid4():
    pass


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Model": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
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
        "/valid1": {
            "get": {
                "summary": "Valid1",
                "operationId": "valid1_valid1_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "500": {
                        "content": {"application/json": {"schema": {"type": "integer"}}}
                    },
                },
            }
        },
        "/valid2": {
            "get": {
                "summary": "Valid2",
                "operationId": "valid2_valid2_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "500": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                }
                            }
                        }
                    },
                },
            }
        },
        "/valid3": {
            "get": {
                "summary": "Valid3",
                "operationId": "valid3_valid3_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "500": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Model"}
                            }
                        }
                    },
                },
            }
        },
        "/valid4": {
            "get": {
                "summary": "Valid4",
                "operationId": "valid4_valid4_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "500": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Model"},
                                }
                            }
                        }
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


def test_path_operations():
    response = client.get("/valid1")
    assert response.status_code == 200, response.text
    response = client.get("/valid2")
    assert response.status_code == 200, response.text
    response = client.get("/valid3")
    assert response.status_code == 200, response.text
    response = client.get("/valid4")
    assert response.status_code == 200, response.text
