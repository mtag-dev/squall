from dataclasses import dataclass

from squall import Body, Cookie, Header, Path, Query, Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class Item:
    data: str


@app.post("/schema_extra")
def schema_extra(item: Item):
    return item


@app.post("/example")
def example(item: Item = Body(..., example={"data": "Data in Body example"})):
    return item


@app.post("/examples")
def examples(
    item: Item = Body(
        ...,
        examples={
            "example1": {
                "summary": "example1 summary",
                "value": {"data": "Data in Body examples, example1"},
            },
            "example2": {"value": {"data": "Data in Body examples, example2"}},
        },
    )
):
    return item


@app.post("/example_examples")
def example_examples(
    item: Item = Body(
        ...,
        example={"data": "Overriden example"},
        examples={
            "example1": {"value": {"data": "examples example_examples 1"}},
            "example2": {"value": {"data": "examples example_examples 2"}},
        },
    )
):
    return item


# TODO: enable these tests once/if Form(embed=False) is supported
# TODO: In that case, define if File() should support example/examples too
# @app.post("/form_example")
# def form_example(firstname: str = Form(..., example="John")):
#     return firstname


# @app.post("/form_examples")
# def form_examples(
#     lastname: str = Form(
#         ...,
#         examples={
#             "example1": {"summary": "last name summary", "value": "Doe"},
#             "example2": {"value": "Doesn't"},
#         },
#     ),
# ):
#     return lastname


# @app.post("/form_example_examples")
# def form_example_examples(
#     lastname: str = Form(
#         ...,
#         example="Doe overriden",
#         examples={
#             "example1": {"summary": "last name summary", "value": "Doe"},
#             "example2": {"value": "Doesn't"},
#         },
#     ),
# ):
#     return lastname


@app.get("/path_example/{item_id}")
def path_example(
    item_id: str = Path(
        ...,
        example="item_1",
    ),
):
    return item_id


@app.get("/path_examples/{item_id}")
def path_examples(
    item_id: str = Path(
        ...,
        examples={
            "example1": {"summary": "item ID summary", "value": "item_1"},
            "example2": {"value": "item_2"},
        },
    ),
):
    return item_id


@app.get("/path_example_examples/{item_id}")
def path_example_examples(
    item_id: str = Path(
        ...,
        example="item_overriden",
        examples={
            "example1": {"summary": "item ID summary", "value": "item_1"},
            "example2": {"value": "item_2"},
        },
    ),
):
    return item_id


@app.get("/query_example")
def query_example(
    data: str = Query(
        None,
        example="query1",
    ),
):
    return data


@app.get("/query_examples")
def query_examples(
    data: str = Query(
        None,
        examples={
            "example1": {"summary": "Query example 1", "value": "query1"},
            "example2": {"value": "query2"},
        },
    ),
):
    return data


@app.get("/query_example_examples")
def query_example_examples(
    data: str = Query(
        None,
        example="query_overriden",
        examples={
            "example1": {"summary": "Qeury example 1", "value": "query1"},
            "example2": {"value": "query2"},
        },
    ),
):
    return data


@app.get("/header_example")
def header_example(
    data: str = Header(
        None,
        example="header1",
    ),
):
    return data


@app.get("/header_examples")
def header_examples(
    data: str = Header(
        None,
        examples={
            "example1": {"summary": "header example 1", "value": "header1"},
            "example2": {"value": "header2"},
        },
    ),
):
    return data


@app.get("/header_example_examples")
def header_example_examples(
    data: str = Header(
        None,
        example="header_overriden",
        examples={
            "example1": {"summary": "Qeury example 1", "value": "header1"},
            "example2": {"value": "header2"},
        },
    ),
):
    return data


@app.get("/cookie_example")
def cookie_example(
    data: str = Cookie(
        None,
        example="cookie1",
    ),
):
    return data


@app.get("/cookie_examples")
def cookie_examples(
    data: str = Cookie(
        None,
        examples={
            "example1": {"summary": "cookie example 1", "value": "cookie1"},
            "example2": {"value": "cookie2"},
        },
    ),
):
    return data


@app.get("/cookie_example_examples")
def cookie_example_examples(
    data: str = Cookie(
        None,
        example="cookie_overriden",
        examples={
            "example1": {"summary": "Qeury example 1", "value": "cookie1"},
            "example2": {"value": "cookie2"},
        },
    ),
):
    return data


client = TestClient(app)


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "properties": {"data": {"type": "string"}},
                "required": ["data"],
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
        "/schema_extra": {
            "post": {
                "summary": "Schema Extra",
                "operationId": "schema_extra_schema_extra_post",
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
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                },
            }
        },
        "/example": {
            "post": {
                "summary": "Example",
                "operationId": "example_example_post",
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
                    "required": None,
                    "content": {
                        "application/json": {
                            "example": {"data": "Data in Body example"},
                            "schema": {"$ref": "#/components/schemas/Item"},
                        }
                    },
                },
            }
        },
        "/examples": {
            "post": {
                "summary": "Examples",
                "operationId": "examples_examples_post",
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
                    "required": None,
                    "content": {
                        "application/json": {
                            "examples": {
                                "example1": {
                                    "summary": "example1 summary",
                                    "value": {
                                        "data": "Data in Body examples, example1"
                                    },
                                },
                                "example2": {
                                    "value": {"data": "Data in Body examples, example2"}
                                },
                            },
                            "schema": {"$ref": "#/components/schemas/Item"},
                        }
                    },
                },
            }
        },
        "/example_examples": {
            "post": {
                "summary": "Example Examples",
                "operationId": "example_examples_example_examples_post",
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
                    "required": None,
                    "content": {
                        "application/json": {
                            "examples": {
                                "example1": {
                                    "value": {"data": "examples example_examples 1"}
                                },
                                "example2": {
                                    "value": {"data": "examples example_examples 2"}
                                },
                            },
                            "schema": {"$ref": "#/components/schemas/Item"},
                        }
                    },
                },
            }
        },
        "/path_example/{item_id}": {
            "get": {
                "summary": "Path Example",
                "operationId": "path_example_path_example__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                        "example": "item_1",
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
        "/path_examples/{item_id}": {
            "get": {
                "summary": "Path Examples",
                "operationId": "path_examples_path_examples__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                        "examples": {
                            "example1": {
                                "summary": "item ID summary",
                                "value": "item_1",
                            },
                            "example2": {"value": "item_2"},
                        },
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
        "/path_example_examples/{item_id}": {
            "get": {
                "summary": "Path Example Examples",
                "operationId": "path_example_examples_path_example_examples__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                        "example": "item_overriden",
                        "examples": {
                            "example1": {
                                "summary": "item ID summary",
                                "value": "item_1",
                            },
                            "example2": {"value": "item_2"},
                        },
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
        "/query_example": {
            "get": {
                "summary": "Query Example",
                "operationId": "query_example_query_example_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "query",
                        "example": "query1",
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
        "/query_examples": {
            "get": {
                "summary": "Query Examples",
                "operationId": "query_examples_query_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "query",
                        "examples": {
                            "example1": {
                                "summary": "Query example 1",
                                "value": "query1",
                            },
                            "example2": {"value": "query2"},
                        },
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
        "/query_example_examples": {
            "get": {
                "summary": "Query Example Examples",
                "operationId": "query_example_examples_query_example_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "query",
                        "example": "query_overriden",
                        "examples": {
                            "example1": {
                                "summary": "Qeury example 1",
                                "value": "query1",
                            },
                            "example2": {"value": "query2"},
                        },
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
        "/header_example": {
            "get": {
                "summary": "Header Example",
                "operationId": "header_example_header_example_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "header",
                        "example": "header1",
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
        "/header_examples": {
            "get": {
                "summary": "Header Examples",
                "operationId": "header_examples_header_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "header",
                        "examples": {
                            "example1": {
                                "summary": "header example 1",
                                "value": "header1",
                            },
                            "example2": {"value": "header2"},
                        },
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
        "/header_example_examples": {
            "get": {
                "summary": "Header Example Examples",
                "operationId": "header_example_examples_header_example_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "header",
                        "example": "header_overriden",
                        "examples": {
                            "example1": {
                                "summary": "Qeury example 1",
                                "value": "header1",
                            },
                            "example2": {"value": "header2"},
                        },
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
        "/cookie_example": {
            "get": {
                "summary": "Cookie Example",
                "operationId": "cookie_example_cookie_example_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "cookie",
                        "example": "cookie1",
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
        "/cookie_examples": {
            "get": {
                "summary": "Cookie Examples",
                "operationId": "cookie_examples_cookie_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "cookie",
                        "examples": {
                            "example1": {
                                "summary": "cookie example 1",
                                "value": "cookie1",
                            },
                            "example2": {"value": "cookie2"},
                        },
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
        "/cookie_example_examples": {
            "get": {
                "summary": "Cookie Example Examples",
                "operationId": "cookie_example_examples_cookie_example_examples_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "data",
                        "in": "cookie",
                        "example": "cookie_overriden",
                        "examples": {
                            "example1": {
                                "summary": "Qeury example 1",
                                "value": "cookie1",
                            },
                            "example2": {"value": "cookie2"},
                        },
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
    """
    Test that example overrides work:

    * model schema_extra is included
    * Body(example={}) overrides schema_extra in model
    * Body(examples{}) overrides Body(example={}) and schema_extra in model
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_call_api():
    response = client.post("/schema_extra", json={"data": "Foo"})
    assert response.status_code == 200, response.text
    response = client.post("/example", json={"data": "Foo"})
    assert response.status_code == 200, response.text
    response = client.post("/examples", json={"data": "Foo"})
    assert response.status_code == 200, response.text
    response = client.post("/example_examples", json={"data": "Foo"})
    assert response.status_code == 200, response.text
    response = client.get("/path_example/foo")
    assert response.status_code == 200, response.text
    response = client.get("/path_examples/foo")
    assert response.status_code == 200, response.text
    response = client.get("/path_example_examples/foo")
    assert response.status_code == 200, response.text
    response = client.get("/query_example")
    assert response.status_code == 200, response.text
    response = client.get("/query_examples")
    assert response.status_code == 200, response.text
    response = client.get("/query_example_examples")
    assert response.status_code == 200, response.text
    response = client.get("/header_example")
    assert response.status_code == 200, response.text
    response = client.get("/header_examples")
    assert response.status_code == 200, response.text
    response = client.get("/header_example_examples")
    assert response.status_code == 200, response.text
    response = client.get("/cookie_example")
    assert response.status_code == 200, response.text
    response = client.get("/cookie_examples")
    assert response.status_code == 200, response.text
    response = client.get("/cookie_example_examples")
    assert response.status_code == 200, response.text
