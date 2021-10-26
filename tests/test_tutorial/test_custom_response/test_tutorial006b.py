import pytest

from docs_src.custom_response.tutorial006b import app
from squall.testclient import TestClient

client = TestClient(app)


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.0.1"},
    "paths": {
        "/squall": {
            "get": {
                "summary": "Redirect Squall",
                "operationId": "redirect_squall_squall_get",
                "responses": {"307": {"description": "Successful Response"}},
            }
        }
    },
}


@pytest.mark.skip("fix")
def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_redirect_response_class():
    response = client.get("/squall", allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://squall.mtag.dev"
