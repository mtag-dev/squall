from squall.router import RootRouter, Router


def test_sub_router():
    v1_router = Router(prefix="/v1")
    user_router = Router(prefix="/user")
    user_router.add_api_route(
        "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        methods=["GET", "POST"],
        endpoint=lambda *a: {},
    )
    v1_router.include_router(user_router)

    router = RootRouter(prefix="/api")
    router.include_router(v1_router)

    assert router.routes[0].path == "".join(
        [
            "/api",
            "/v1",
            "/user",
            "/some/prefix(?P<some>[^/]+)/item/(?P<item>[^/]+)/(?P<more>[^/]+)-suffix",
        ]
    )
