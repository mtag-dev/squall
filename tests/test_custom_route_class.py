import pytest
from squall import Router, Squall
from squall.routing import APIRoute
from squall.testclient import TestClient
from starlette.routing import Route

app = Squall()


class APIRouteA(APIRoute):
    x_type = "A"


class APIRouteB(APIRoute):
    x_type = "B"


class APIRouteC(APIRoute):
    x_type = "C"


router_a = Router(route_class=APIRouteA, prefix="/a")
router_b = Router(route_class=APIRouteB, prefix="/b")
router_c = Router(route_class=APIRouteC, prefix="/c")


@router_a.get("/")
def get_a():
    return {"msg": "A"}


@router_b.get("/")
def get_b():
    return {"msg": "B"}


@router_c.get("/")
def get_c():
    return {"msg": "C"}


router_b.include_router(router=router_c)
router_a.include_router(router=router_b)
app.include_router(router=router_a)


client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "paths": {
        "/a/": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
                "summary": "Get A",
                "operationId": "get_a_a__get",
            }
        },
        "/a/b/": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
                "summary": "Get B",
                "operationId": "get_b_a_b__get",
            }
        },
        "/a/b/c/": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
                "summary": "Get C",
                "operationId": "get_c_a_b_c__get",
            }
        },
    },
}


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/a", 200, {"msg": "A"}),
        ("/a/b", 200, {"msg": "B"}),
        ("/a/b/c", 200, {"msg": "C"}),
        ("/openapi.json", 200, openapi_schema),
    ],
)
def test_get_path(path, expected_status, expected_response):
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.json() == expected_response


def test_route_classes():
    routes = {}
    for r in app.router.routes:
        assert isinstance(r, Route)
        routes[r.path] = r
    assert getattr(routes["/a/"], "x_type") == "A"
    assert getattr(routes["/a/b/"], "x_type") == "B"
    assert getattr(routes["/a/b/c/"], "x_type") == "C"
