from squall import HTTPException, Num, Path, Squall
from squall.exceptions import RequestPayloadValidationError
from squall.responses import PrettyJSONResponse
from squall.testclient import TestClient


def http_exception_handler(request, exception):
    return PrettyJSONResponse({"exception": "http-exception"})


def request_validation_exception_handler(request, exception):
    return PrettyJSONResponse({"exception": "request-validation"})


app = Squall(
    exception_handlers={
        HTTPException: http_exception_handler,
        RequestPayloadValidationError: request_validation_exception_handler,
    }
)

client = TestClient(app)


@app.get("/http-exception")
def route_with_http_exception():
    raise HTTPException(status_code=400)


@app.get("/request-validation/{param}")
def route_with_request_validation_exception(param: int = Path(valid=Num(ge=5))):
    raise ValueError(param)
    pass  # pragma: no cover


def test_override_http_exception():
    response = client.get("/http-exception")
    assert response.status_code == 200
    assert response.json() == {"exception": "http-exception"}


def test_override_request_validation_exception():
    response = client.get("/request-validation/3")
    assert response.status_code == 400
    assert response.json() == {
        "details": [
            {"loc": ["path_params", "param"], "msg": "Validation error", "val": 3}
        ]
    }
