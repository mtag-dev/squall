import squall.routing.router


def test_add_api_route_defaults(mocker):
    route = mocker.MagicMock()
    endpoint = mocker.Mock()
    router = squall.routing.router.Router(route_class=route)
    router.add_api_route("/mocked", methods=["GET"], endpoint=endpoint)
    route.assert_called_once_with(
        "/mocked",
        endpoint=endpoint,
        response_model=None,
        status_code=None,
        tags=[],
        summary=None,
        description=None,
        response_description="Successful Response",
        responses={},
        deprecated=None,
        methods=["GET"],
        operation_id=None,
        include_in_schema=True,
        response_class=squall.routing.router.JSONResponse,
        name=None,
        openapi_extra=None,
    )


def test_add_api_route_custom(mocker):
    route = mocker.MagicMock()
    response_model = mocker.Mock()
    response_class = mocker.Mock()
    status_code = 200
    tags = ["happiness"]
    [mocker.Mock()]
    summary = "summary"
    description = "description"
    response_description = "response_description"
    responses = {"404": "Not found"}
    deprecated = True
    operation_id = "operation_id"

    endpoint = mocker.Mock()
    router = squall.routing.router.Router(route_class=route)
    router.add_api_route(
        "/mocked",
        methods=["GET"],
        endpoint=endpoint,
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        operation_id=operation_id,
        include_in_schema=False,
        response_class=response_class,
        name="mocked",
        openapi_extra={"extra": "data"},
    )
    route.assert_called_once_with(
        "/mocked",
        endpoint=endpoint,
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        methods=["GET"],
        operation_id=operation_id,
        include_in_schema=False,
        response_class=response_class,
        name="mocked",
        openapi_extra={"extra": "data"},
    )


def test_sub_routing():
    user_router = squall.routing.router.Router(prefix="/user")
    user_router.add_api_route(
        "/some/{some}/item/{item}",
        methods=["GET", "POST"],
        endpoint=lambda *a: {},
    )
    v1_router = squall.routing.router.Router(prefix="/v1")
    v1_router.include_router(user_router)
    router = squall.routing.router.Router(prefix="/api")
    router.include_router(v1_router)

    assert router._routes[0].path.path == "".join(
        [
            "/api",
            "/v1",
            "/user",
            "/some/{some}/item/{item}",
        ]
    )

    # Check that second coll didn't add extra path prefix
    assert router._routes[0].path.path == "".join(
        [
            "/api",
            "/v1",
            "/user",
            "/some/{some}/item/{item}",
        ]
    )
