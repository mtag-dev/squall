from unittest.mock import patch

import pytest
from squall.testclient import TestClient

from docs_src.body.tutorial001 import app

client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "paths": {
        "/items/": {
            "post": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
                "summary": "Create Item",
                "operationId": "create_item_items__post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                    "required": True,
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Item": {
                "title": "Item",
                "required": ["name", "price"],
                "type": "object",
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "price": {"title": "Price", "type": "number"},
                    "description": {"title": "Description", "type": "string"},
                    "tax": {"title": "Tax", "type": "number"},
                },
            },
            "ValidationError": {
                "title": "ValidationError",
                "required": ["loc", "msg", "type"],
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
        }
    },
}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


price_missing = {
    "detail": [
        {
            "loc": ["body", "price"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
}

price_not_float = {
    "detail": [
        {
            "loc": ["body", "price"],
            "msg": "value is not a valid float",
            "type": "type_error.float",
        }
    ]
}

name_price_missing = {
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", "price"],
            "msg": "field required",
            "type": "value_error.missing",
        },
    ]
}

body_missing = {
    "detail": [
        {"loc": ["body"], "msg": "field required", "type": "value_error.missing"}
    ]
}


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/items/",
            {"name": "Foo", "price": 50.5},
            200,
            {"name": "Foo", "price": 50.5, "description": None, "tax": None},
        ),
        (
            "/items/",
            {"name": "Foo", "price": "50.5"},
            200,
            {"name": "Foo", "price": 50.5, "description": None, "tax": None},
        ),
        (
            "/items/",
            {"name": "Foo", "price": "50.5", "description": "Some Foo"},
            200,
            {"name": "Foo", "price": 50.5, "description": "Some Foo", "tax": None},
        ),
        (
            "/items/",
            {"name": "Foo", "price": "50.5", "description": "Some Foo", "tax": 0.3},
            200,
            {"name": "Foo", "price": 50.5, "description": "Some Foo", "tax": 0.3},
        ),
        ("/items/", {"name": "Foo"}, 422, price_missing),
        ("/items/", {"name": "Foo", "price": "twenty"}, 422, price_not_float),
        ("/items/", {}, 422, name_price_missing),
        ("/items/", None, 422, body_missing),
    ],
)
def test_post_body(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.json() == expected_response


def test_post_broken_body():
    response = client.post(
        "/items/",
        headers={"content-type": "application/json"},
        data="{some broken json}",
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", 1],
                "msg": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
                "type": "value_error.jsondecode",
                "ctx": {
                    "msg": "Expecting property name enclosed in double quotes",
                    "doc": "{some broken json}",
                    "pos": 1,
                    "lineno": 1,
                    "colno": 2,
                },
            }
        ]
    }


def test_post_form_for_json():
    response = client.post("/items/", data={"name": "Foo", "price": 50.5})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "ctx": {"class_name": "Item"},
                "loc": ["body"],
                "msg": "instance of Item, tuple or dict expected",
                "type": "type_error.dataclass",
            }
        ]
    }


def test_explicit_content_type():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, response.text


def test_geo_json():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
        headers={"Content-Type": "application/geo+json"},
    )
    assert response.status_code == 200, response.text


def test_no_content_type_is_json():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "name": "Foo",
        "description": None,
        "price": 50.5,
        "tax": None,
    }


def test_wrong_headers():
    data = '{"name": "Foo", "price": 50.5}'
    invalid_dict = {
        "detail": [
            {
                "loc": ["body"],
                "ctx": {"class_name": "Item"},
                "msg": "instance of Item, tuple or dict expected",
                "type": "type_error.dataclass",
            }
        ]
    }

    response = client.post("/items/", data=data, headers={"Content-Type": "text/plain"})
    assert response.status_code == 422, response.text
    assert response.json() == invalid_dict

    response = client.post(
        "/items/", data=data, headers={"Content-Type": "application/geo+json-seq"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == invalid_dict
    response = client.post(
        "/items/", data=data, headers={"Content-Type": "application/not-really-json"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == invalid_dict


def test_other_exceptions():
    with patch("json.loads", side_effect=Exception):
        response = client.post("/items/", json={"test": "test2"})
        assert response.status_code == 400, response.text
