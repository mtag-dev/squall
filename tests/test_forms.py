import pytest
from squall import File, Form, Squall, UploadFile
from squall.testclient import TestClient

app = Squall()


@app.post("/files/")
async def create_file(
    file: UploadFile = File(...), fileb: UploadFile = File(...), token: str = Form(...)
):
    file = await file.read()
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }


client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "FastAPI", "version": "0.1.0"},
    "paths": {
        "/files/": {
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
                "summary": "Create File",
                "operationId": "create_file_files__post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "$ref": "#/components/schemas/Body_create_file_files__post"
                            }
                        }
                    },
                    "required": True,
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Body_create_file_files__post": {
                "title": "Body_create_file_files__post",
                "required": ["file", "fileb", "token"],
                "type": "object",
                "properties": {
                    "file": {"title": "File", "type": "string", "format": "binary"},
                    "fileb": {"title": "Fileb", "type": "string", "format": "binary"},
                    "token": {"title": "Token", "type": "string"},
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


@pytest.mark.skip("Not implemented")
def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


file_required = {
    "details": [
        {"loc": ["form", "file"], "msg": "field required"},
        {"loc": ["form", "fileb"], "msg": "field required"},
    ]
}

error_parsing_body = {"detail": "There was an error parsing the body"}

file_and_token_required = {
    "details": [
        {"loc": ["form", "file"], "msg": "field required"},
        {"loc": ["form", "fileb"], "msg": "field required"},
        {"loc": ["form", "token"], "msg": "field required"},
    ]
}


def test_post_form_no_body():
    response = client.post("/files/")
    assert response.status_code == 400, response.text
    assert response.json() == error_parsing_body


def test_post_form_no_file():
    response = client.post("/files/", data={"token": "foo"})
    assert response.status_code == 400, response.text
    assert response.json() == error_parsing_body


def test_post_body_json():
    response = client.post("/files/", json={"file": "Foo", "token": "Bar"})
    assert response.status_code == 400, response.text
    assert response.json() == error_parsing_body


def test_post_file_no_token(tmp_path):
    path = tmp_path / "test.txt"
    path.write_bytes(b"<file content>")

    client = TestClient(app)
    with path.open("rb") as file:
        response = client.post("/files/", files={"file": file})
    assert response.status_code == 400, response.text
    assert response.json() == error_parsing_body


def test_post_files_and_token(tmp_path):
    patha = tmp_path / "test.txt"
    pathb = tmp_path / "testb.txt"
    patha.write_text("<file content>")
    pathb.write_text("<file b content>")

    client = TestClient(app)
    with patha.open("rb") as filea, pathb.open("rb") as fileb:
        response = client.post(
            "/files/",
            data={"token": "foo"},
            files={"file": filea, "fileb": ("testb.txt", fileb, "text/plain")},
        )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "file_size": 14,
        "token": "foo",
        "fileb_content_type": "text/plain",
    }
