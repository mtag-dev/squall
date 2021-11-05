import typing

from pydantic import BaseModel
from squall import Squall
from squall.responses import JSONResponse
from squall.testclient import TestClient

app = Squall()


class JsonApiResponse(JSONResponse):
    media_type = "application/vnd.api+json"


class Error(BaseModel):
    status: str
    title: str


class JsonApiError(BaseModel):
    errors: typing.List[Error]


@app.router.get(
    "/a/{id}",
    response_class=JsonApiResponse,
    responses={422: {"description": "Error", "model": JsonApiError}},
)
async def a(id):
    pass  # pragma: no cover


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "paths": {
        "/a/{id}": {
            "get": {
                "responses": {
                    "422": {
                        "description": "Error",
                        "content": {
                            "application/vnd.api+json": {
                                "schema": {"$ref": "#/components/schemas/JsonApiError"}
                            }
                        },
                    },
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/vnd.api+json": {"schema": {}}},
                    },
                },
                "summary": "A",
                "operationId": "a_a__id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"title": "Id"},
                        "name": "id",
                        "in": "path",
                    }
                ],
            }
        }
    },
    "components": {
        "schemas": {
            "Error": {
                "title": "Error",
                "required": ["status", "title"],
                "type": "object",
                "properties": {
                    "status": {"title": "Status", "type": "string"},
                    "title": {"title": "Title", "type": "string"},
                },
            },
            "JsonApiError": {
                "title": "JsonApiError",
                "required": ["errors"],
                "type": "object",
                "properties": {
                    "errors": {
                        "title": "Errors",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Error"},
                    }
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
