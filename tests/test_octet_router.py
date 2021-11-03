import pytest
from squall.routing import APIRoute, OctetRouter


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/some/item/static", ["some", "item", "static"]),
        (
            "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
            ["some", "*", "item", "*", "*"],
        ),
        (
            "/some/prefix{some_id}/item/{item_id}/extra/{extra}-suffix",
            ["some", "*", "item", "*", "extra", "*"],
        ),
        (
            "/some/{some_id}/item/{item_id}/extra/(?P<username>[^/]+)-dw/company/",
            ["some", "*", "item", "*", "extra", "*", "company"],
        ),
    ],
)
def test_route_octets(path, expected):
    assert OctetRouter.get_path_octets(path) == expected


def test_add_route():
    router = OctetRouter()
    route1 = APIRoute(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        lambda *a: {},
        methods=["GET", "POST"],
    )
    route2 = APIRoute(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        lambda *a: {},
        methods=["PATCH", "DELETE"],
    )
    router.add_route(route1)
    router.add_route(route2)
    assert route1 in router._routes["some"]["*"]["item"]["*"]["*"]["#handlers#"]["GET"]
    assert route1 in router._routes["some"]["*"]["item"]["*"]["*"]["#handlers#"]["POST"]
    assert (
        route2 in router._routes["some"]["*"]["item"]["*"]["*"]["#handlers#"]["PATCH"]
    )
    assert (
        route2 in router._routes["some"]["*"]["item"]["*"]["*"]["#handlers#"]["DELETE"]
    )


def test_get_handlers():
    router = OctetRouter()
    route1 = APIRoute(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        lambda *a: {},
        methods=["GET", "POST"],
    )
    route2 = APIRoute(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        lambda *a: {},
        methods=["PATCH", "DELETE"],
    )
    router.add_route(route1)
    router.add_route(route2)
    assert route1 in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "GET"
    )
    assert route1 in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "POST"
    )
    assert route1 not in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "PATCH"
    )
    assert route1 not in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "DELETE"
    )

    assert route2 not in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "GET"
    )
    assert route2 not in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "POST"
    )
    assert route2 in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "PATCH"
    )
    assert route2 in router.get_http_handlers(
        "/some/prefixaaa/item/bbb/ccc-suffix", "DELETE"
    )
