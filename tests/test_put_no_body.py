from squall import Squall
from squall.testclient import TestClient

app = Squall()


@app.put("/items/{item_id}")
def save_item_no_body(item_id: str):
    return {"item_id": item_id}


client = TestClient(app)


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "paths": {
        "/items/{item_id}": {
            "put": {
                "summary": "Save Item No Body",
                "operationId": "save_item_no_body_items__item_id__put",
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
        }
    },
}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_put_no_body():
    response = client.put("/items/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_put_no_body_with_body():
    response = client.put("/items/foo", json={"name": "Foo"})
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}
