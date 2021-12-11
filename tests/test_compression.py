import pytest
from squall import Squall
from squall.compression import Compression, GzipBackend, ZlibBackend
from squall.responses import HTMLResponse, JSONResponse, PlainTextResponse
from squall.testclient import TestClient


@pytest.mark.parametrize(
    "backends",
    [
        [GzipBackend(), ZlibBackend()],
        [ZlibBackend()],
        [GzipBackend()],
    ],
)
def test_compression_backends(backends):
    app = Squall(compression=Compression(backends=backends, minimum_size=1))

    @app.get("/")
    def get_root():
        return {"msg": "Hello World"}

    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"msg": "Hello World"}


@pytest.mark.parametrize(
    "response_class,response,expected_response",
    [
        [HTMLResponse, "Hello World", b"Hello World"],
        [JSONResponse, {"msg": "Hello World"}, b'{"msg":"Hello World"}'],
        [PlainTextResponse, "Hello World", b"Hello World"],
    ],
)
def test_compression_response_classes(response_class, response, expected_response):
    app = Squall(compression=Compression(minimum_size=1))

    @app.get("/", response_class=response_class)
    def get_root():
        return response

    client = TestClient(app)
    response = client.get("/")
    assert response.content == expected_response
