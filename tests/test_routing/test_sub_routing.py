from squall.routing.router import RootRouter, Router


def test_sub_router():
    v1_router = Router(prefix="/v1")
    user_router = Router(prefix="/user")
    user_router.add_api_route(
        "/some/{some}/item/{item}",
        methods=["GET", "POST"],
        endpoint=lambda *a: {},
    )
    v1_router.include_router(user_router)

    router = RootRouter(prefix="/api")
    router.include_router(v1_router)

    assert router.routes[0].path.path == "".join(
        ["/api", "/v1", "/user", "/some/{some}/item/{item}"]
    )
