from dataclasses import dataclass, field
from typing import Optional

from squall import Squall
from squall.responses import JSONResponse
from squall.testclient import TestClient

app = Squall()


@dataclass
class Item:
    name: str = field()
    price: Optional[float] = None


@app.add_api("/items/{item_id}", methods=["GET"])
def get_items(item_id: str):
    return {"item_id": item_id}


def get_not_decorated(item_id: str):
    return {"item_id": item_id}


app.add_api_route("/items-not-decorated/{item_id}", get_not_decorated)


@app.delete("/items/{item_id}")
def delete_item(item_id: str, item: Item):
    return {"item_id": item_id, "item": item}


@app.head("/items/{item_id}")
def head_item(item_id: str):
    return JSONResponse(headers={"x-squall-item-id": item_id})


@app.options("/items/{item_id}")
def options_item(item_id: str):
    return JSONResponse(headers={"x-squall-item-id": item_id})


@app.patch("/items/{item_id}")
def patch_item(item_id: str, item: Item):
    return {"item_id": item_id, "item": item}


@app.trace("/items/{item_id}")
def trace_item(item_id: str):
    return JSONResponse(media_type="message/http")


client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": ["number", "null"], "default": None},
                },
                "required": ["name"],
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
        "/items/{item_id}": {
            "get": {
                "summary": "Get Items",
                "operationId": "get_items_items__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            },
            "delete": {
                "summary": "Delete Item",
                "operationId": "delete_item_items__item_id__delete",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
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
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                },
            },
            "head": {
                "summary": "Head Item",
                "operationId": "head_item_items__item_id__head",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            },
            "options": {
                "summary": "Options Item",
                "operationId": "options_item_items__item_id__options",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            },
            "patch": {
                "summary": "Patch Item",
                "operationId": "patch_item_items__item_id__patch",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
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
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                },
            },
            "trace": {
                "summary": "Trace Item",
                "operationId": "trace_item_items__item_id__trace",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            },
        },
        "/items-not-decorated/{item_id}": {
            "get": {
                "summary": "Get Not Decorated",
                "operationId": "get_not_decorated_items_not_decorated__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
    },
}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_get_api_route():
    response = client.get("/items/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_get_api_route_not_decorated():
    response = client.get("/items-not-decorated/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_delete():
    response = client.delete("/items/foo", json={"name": "Foo"})
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo", "item": {"name": "Foo", "price": None}}


def test_head():
    response = client.head("/items/foo")
    assert response.status_code == 200, response.text
    assert response.headers["x-squall-item-id"] == "foo"


def test_options():
    response = client.options("/items/foo")
    assert response.status_code == 200, response.text
    assert response.headers["x-squall-item-id"] == "foo"


def test_patch():
    response = client.patch("/items/foo", json={"name": "Foo"})
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo", "item": {"name": "Foo", "price": None}}


def test_trace():
    response = client.request("trace", "/items/foo")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "message/http"
