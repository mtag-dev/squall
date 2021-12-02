from squall import Router, Squall
from squall.responses import HTMLResponse, JSONResponse, PlainTextResponse
from squall.testclient import TestClient


class OverrideResponse(JSONResponse):
    media_type = "application/x-override"


json_type = "application/json"
text_type = "text/plain; charset=utf-8"
html_type = "text/html; charset=utf-8"
override_type = "application/x-override"


def test_defaults():
    app = Squall()
    router = Router(prefix="/r")

    @router.get("/")
    def get_root():
        return {"msg": "Hello World"}

    app.include_router(router)
    client = TestClient(app)
    response = client.get("/r")
    assert response.json() == {"msg": "Hello World"}
    assert response.headers["content-type"] == json_type


def test_override():
    app = Squall()
    router = Router(prefix="/r", default_response_class=OverrideResponse)

    @router.get("/override")
    def get_default():
        return {"msg": "Hello World"}

    @router.get("/text", response_class=PlainTextResponse)
    def get_overridden():
        return "Hello World"

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/r/override")
    assert response.json() == {"msg": "Hello World"}
    assert response.headers["content-type"] == override_type

    response = client.get("/r/text")
    assert response.text == "Hello World"
    assert response.headers["content-type"] == text_type


def test_nesting():
    app = Squall()
    router = Router(prefix="/r", default_response_class=OverrideResponse)
    nested_router = Router(prefix="/n", default_response_class=HTMLResponse)

    @nested_router.get("/html")
    def get_default_nested():
        return "Hello HTML"

    @router.get("/override")
    def get_default():
        return {"msg": "Hello World"}

    @router.get("/text", response_class=PlainTextResponse)
    def get_overridden():
        return "Hello World"

    router.include_router(nested_router)
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/r/override")
    assert response.json() == {"msg": "Hello World"}
    assert response.headers["content-type"] == override_type

    response = client.get("/r/text")
    assert response.text == "Hello World"
    assert response.headers["content-type"] == text_type

    response = client.get("/r/n/html")
    assert response.text == "Hello HTML"
    assert response.headers["content-type"] == html_type
