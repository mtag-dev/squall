import http
from typing import Optional

import pytest
from squall import Query, Squall
from squall.testclient import TestClient

app = Squall()


@app.get("/query")
def get_query(query=Query(...)):
    return f"foo bar {query}"


@app.get("/query/optional")
def get_query_optional(query=Query(None)):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@app.get("/query/int")
def get_query_type(query: int = Query(...)):
    return f"foo bar {query}"


@app.get("/query/int/optional")
def get_query_type_optional(query: Optional[int] = Query(None)):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@app.get("/query/int/default")
def get_query_type_int_default(query: int = Query(10)):
    return f"foo bar {query}"


@app.get("/query/param")
def get_query_param(query=Query(None)):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@app.get("/query/param-required")
def get_query_param_required(query=Query(...)):
    return f"foo bar {query}"


@app.get("/query/param-required/int")
def get_query_param_required_type(query: int = Query(...)):
    return f"foo bar {query}"


@app.get("/enum-status-code", status_code=http.HTTPStatus.CREATED)
def get_enum_status_code():
    return "foo bar"


client = TestClient(app)

response_missing = {
    "details": [{"loc": ["query_params", "query"], "msg": "Mandatory field missed"}]
}

response_not_valid_int = {
    "details": [
        {"loc": ["query_params", "query"], "msg": "Cast of `int` failed", "val": "foo"}
    ]
}


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/query", 400, response_missing),
        ("/query?query=baz", 200, "foo bar baz"),
        ("/query?not_declared=baz", 400, response_missing),
        ("/query/optional", 200, "foo bar"),
        ("/query/optional?query=baz", 200, "foo bar baz"),
        ("/query/optional?not_declared=baz", 200, "foo bar"),
        ("/query/int", 400, response_missing),
        ("/query/int?query=42", 200, "foo bar 42"),
        ("/query/int?query=foo", 400, response_not_valid_int),
        ("/query/int?not_declared=baz", 400, response_missing),
        ("/query/int/optional", 200, "foo bar"),
        ("/query/int/optional?query=50", 200, "foo bar 50"),
        ("/query/int/optional?query=foo", 400, response_not_valid_int),
        ("/query/int/default", 200, "foo bar 10"),
        ("/query/int/default?query=50", 200, "foo bar 50"),
        ("/query/int/default?query=foo", 400, response_not_valid_int),
    ],
)
def test_get_path(path, expected_status, expected_response):
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.json() == expected_response
