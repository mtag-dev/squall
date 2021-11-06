import pytest
from squall.router import RootRouter


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
def test_get_fast_path_octets(path, expected):
    assert RootRouter._get_fast_path_octets(path) == expected


def test_fast_path_routing(mocker):
    router = RootRouter()
    endpoint1 = mocker.Mock()
    endpoint2 = mocker.Mock()
    endpoint_ws = mocker.Mock()

    router.add_api_route(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        endpoint1,
        methods=["GET", "POST"],
    )
    router.add_api_route(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        endpoint2,
        methods=["PUT", "DELETE"],
    )
    router.add_ws_route(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        endpoint_ws,
    )

    assert (
        router._fast_path_route_http["some"]["*"]["item"]["*"]["*"]["#routes#"]["GET"][
            0
        ].endpoint
        == endpoint1
    )
    assert (
        router._fast_path_route_http["some"]["*"]["item"]["*"]["*"]["#routes#"]["POST"][
            0
        ].endpoint
        == endpoint1
    )
    assert (
        router._fast_path_route_http["some"]["*"]["item"]["*"]["*"]["#routes#"]["PUT"][
            0
        ].endpoint
        == endpoint2
    )
    assert (
        router._fast_path_route_http["some"]["*"]["item"]["*"]["*"]["#routes#"][
            "DELETE"
        ][0].endpoint
        == endpoint2
    )
    assert (
        router._fast_path_route_ws["some"]["*"]["item"]["*"]["*"]["#routes#"][
            0
        ].endpoint
        == endpoint_ws
    )

    assert (
        router.get_http_routes("GET", "/some/prefix1/item/1/1-suffix")[0].endpoint
        == endpoint1
    )
    assert (
        router.get_http_routes("POST", "/some/prefix1/item/1/1-suffix")[0].endpoint
        == endpoint1
    )
    assert (
        router.get_http_routes("PUT", "/some/prefix1/item/1/1-suffix")[0].endpoint
        == endpoint2
    )
    assert (
        router.get_http_routes("DELETE", "/some/prefix1/item/1/1-suffix")[0].endpoint
        == endpoint2
    )
    assert (
        router.get_ws_routes("/some/prefix1/item/1/1-suffix")[0].endpoint == endpoint_ws
    )


# def test_get_handlers():
#     router = MainRouter()
#     route1 = APIRoute(
#         "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
#         endpoint=lambda *a: {},
#         methods=["GET", "POST"],
#     )
#     route2 = APIRoute(
#         "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
#         endpoint=lambda *a: {},
#         methods=["PATCH", "DELETE"],
#     )
#     router.add_api_route(route1)
#     router.add_api_route(route2)
#     assert route1 in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "GET"
#     )
#     assert route1 in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "POST"
#     )
#     assert route1 not in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "PATCH"
#     )
#     assert route1 not in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "DELETE"
#     )
#
#     assert route2 not in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "GET"
#     )
#     assert route2 not in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "POST"
#     )
#     assert route2 in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "PATCH"
#     )
#     assert route2 in router.get_http_handlers(
#         "/some/prefixaaa/item/bbb/ccc-suffix", "DELETE"
#     )
