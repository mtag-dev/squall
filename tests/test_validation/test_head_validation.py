import typing
from decimal import Decimal

import pytest
from squall.params import Cookie, Header, Num, Path, Query, Str


def test_no_args(app, client):
    @app.get("/foo")
    def foo():
        return {}

    response = client.get("/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {}


def test_no_defaults_no_annotation(app, client):
    @app.get("/no_defaults/no_annotations/{from_path}")
    def foo(
        from_path, from_qs=Query(...), from_header=Header(...), from_cookie=Cookie(...)
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get("/no_defaults/no_annotations/some_param")
    assert response.status_code == 400, response.text
    assert response.json() == {
        "details": [
            {"loc": ["query_params", "from_qs"], "msg": "Mandatory field missed"},
            {"loc": ["headers", "from_header"], "msg": "Mandatory field missed"},
            {"loc": ["cookies", "from_cookie"], "msg": "Mandatory field missed"},
        ]
    }

    response = client.get(
        "/no_defaults/no_annotations/some_param?from_qs=qs_value",
        headers={"from_header": "header_value"},
        cookies={"from_cookie": "cookie_value"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_path": "some_param",
        "from_path_type": "str",
        "from_qs": "qs_value",
        "from_qs_type": "str",
        "from_header": "header_value",
        "from_header_type": "str",
        "from_cookie": "cookie_value",
        "from_cookie_type": "str",
    }


def test_defaults_no_annotation(app, client):
    @app.get("/defaults/no_annotations")
    def foo(from_qs=Query(None), from_header=Header(None), from_cookie=Cookie(None)):
        return {
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get("/defaults/no_annotations")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_qs": None,
        "from_qs_type": "NoneType",
        "from_header": None,
        "from_header_type": "NoneType",
        "from_cookie": None,
        "from_cookie_type": "NoneType",
    }


def test_parameter_from_another_origin_name(app, client):
    @app.get("/from_another/origin_name/{origin_param}")
    def foo(
        param=Path(..., origin="origin_param"),
        qs=Query(..., origin="origin_qs"),
        header=Header(..., origin="origin_header"),
        cookie=Cookie(..., origin="origin_cookie"),
    ):
        return {
            "param": param,
            "param_type": type(param).__name__,
            "qs": qs,
            "qs_type": type(qs).__name__,
            "header": header,
            "header_type": type(header).__name__,
            "cookie": cookie,
            "cookie_type": type(cookie).__name__,
        }

    response = client.get(
        "/from_another/origin_name/some_param?origin_qs=qs_value",
        headers={"origin_header": "header_value"},
        cookies={"origin_cookie": "cookie_value"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "param": "some_param",
        "param_type": "str",
        "qs": "qs_value",
        "qs_type": "str",
        "header": "header_value",
        "header_type": "str",
        "cookie": "cookie_value",
        "cookie_type": "str",
    }


def test_no_defaults_cast_from_annotation_positive(app, client):
    @app.get("/no_defaults/cast_from_annotation/{from_path}")
    def foo(
        from_path: int,
        from_qs: float = Query(...),
        from_header: str = Header(...),
        from_cookie: bytes = Cookie(...),
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get(
        "/no_defaults/cast_from_annotation/123?from_qs=321",
        headers={"from_header": "header_value"},
        cookies={"from_cookie": "cookie_value"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_path": 123,
        "from_path_type": "int",
        "from_qs": 321.0,
        "from_qs_type": "float",
        "from_header": "header_value",
        "from_header_type": "str",
        "from_cookie": "cookie_value",
        "from_cookie_type": "bytes",
    }


def test_validate_any_string_positive(app, client):
    @app.get("/validate/any_string/{from_path}")
    def foo(
        from_path: str = Path(..., valid=Str(min_len=5, max_len=20)),
        from_qs: str = Query(..., valid=Str(min_len=5, max_len=20)),
        from_header: bytes = Header(..., valid=Str(min_len=5, max_len=20)),
        from_cookie: bytes = Cookie(..., valid=Str(min_len=5, max_len=20)),
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get(
        "/validate/any_string/12345?from_qs=32132",
        headers={"from_header": "header_value"},
        cookies={"from_cookie": "cookie_value"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_path": "12345",
        "from_path_type": "str",
        "from_qs": "32132",
        "from_qs_type": "str",
        "from_header": "header_value",
        "from_header_type": "bytes",
        "from_cookie": "cookie_value",
        "from_cookie_type": "bytes",
    }


@pytest.mark.parametrize(
    "min_len,max_len",
    [
        (6, None),
        (None, 4),
        (1, 4),
    ],
)
def test_validate_any_string_negative(app, client, min_len, max_len):
    @app.get("/validate/any_string/{from_path}")
    def foo(
        from_path: str = Path(..., valid=Str(min_len=min_len, max_len=max_len)),
        from_qs: str = Query(..., valid=Str(min_len=min_len, max_len=max_len)),
        from_header: bytes = Header(..., valid=Str(min_len=min_len, max_len=max_len)),
        from_cookie: bytes = Cookie(..., valid=Str(min_len=min_len, max_len=max_len)),
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get(
        "/validate/any_string/12345?from_qs=12345",
        headers={"from_header": "12345"},
        cookies={"from_cookie": "12345"},
    )
    assert response.status_code == 400, response.text
    assert response.json() == {
        "details": [
            {
                "loc": ["path_params", "from_path"],
                "msg": "Validation error",
                "val": "12345",
            },
            {
                "loc": ["query_params", "from_qs"],
                "msg": "Validation error",
                "val": "12345",
            },
            {
                "loc": ["headers", "from_header"],
                "msg": "Validation error",
                "val": "12345",
            },
            {
                "loc": ["cookies", "from_cookie"],
                "msg": "Validation error",
                "val": "12345",
            },
        ]
    }


def test_validate_numeric_positive(app, client):
    @app.get("/validate/numeric/{from_path}")
    def foo(
        from_path: int = Path(..., valid=Num(ge=5, le=20)),
        from_qs: float = Query(..., valid=Num(ge=5, le=20)),
        from_header: Decimal = Header(..., valid=Num(ge=5, le=20)),
        from_cookie: int = Cookie(..., valid=Num(ge=5, le=20)),
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get(
        "/validate/numeric/15?from_qs=16",
        headers={"from_header": "14"},
        cookies={"from_cookie": "17"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_path": 15,
        "from_path_type": "int",
        "from_qs": 16.0,
        "from_qs_type": "float",
        "from_header": Decimal(14),
        "from_header_type": "Decimal",
        "from_cookie": 17,
        "from_cookie_type": "int",
    }


@pytest.mark.parametrize(
    "ge,le",
    [
        (20, None),
        (None, 5),
        (1, 4),
    ],
)
def test_validate_numeric_negative(app, client, ge, le):
    @app.get("/validate/numeric/{from_path}")
    def foo(
        from_path: int = Path(..., valid=Num(ge=ge, le=le)),
        from_qs: float = Query(..., valid=Num(ge=ge, le=le)),
        from_header: Decimal = Header(..., valid=Num(ge=ge, le=le)),
        from_cookie: int = Cookie(..., valid=Num(ge=ge, le=le)),
    ):
        return {
            "from_path": from_path,
            "from_path_type": type(from_path).__name__,
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_header": from_header,
            "from_header_type": type(from_header).__name__,
            "from_cookie": from_cookie,
            "from_cookie_type": type(from_cookie).__name__,
        }

    response = client.get(
        "/validate/numeric/15?from_qs=16",
        headers={"from_header": "14"},
        cookies={"from_cookie": "17"},
    )
    assert response.status_code == 400, response.text
    assert response.json() == {
        "details": [
            {"loc": ["path_params", "from_path"], "msg": "Validation error", "val": 15},
            {
                "loc": ["query_params", "from_qs"],
                "msg": "Validation error",
                "val": 16.0,
            },
            {"loc": ["headers", "from_header"], "msg": "Validation error", "val": 14.0},
            {"loc": ["cookies", "from_cookie"], "msg": "Validation error", "val": 17},
        ]
    }


def test_list_annotation(app, client):
    @app.get("/validate/any_string/{from_path}")
    def foo(
        from_qs: typing.List[str] = Query(...),
        from_qs2: typing.Optional[typing.List[bytes]] = Query(...),
    ):
        return {
            "from_qs": from_qs,
            "from_qs_type": type(from_qs).__name__,
            "from_qs_element_type": type(from_qs[0]).__name__,
            "from_qs2": from_qs2,
            "from_qs2_type": type(from_qs2).__name__,
            "from_qs2_element_type": type(from_qs2[0]).__name__,
        }

    response = client.get(
        "/validate/any_string/12345?"
        "from_qs=11111&from_qs=22222&"
        "from_qs2=11111&from_qs2=22222"
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "from_qs": ["11111", "22222"],
        "from_qs2": ["11111", "22222"],
        "from_qs2_element_type": "bytes",
        "from_qs2_type": "list",
        "from_qs_element_type": "str",
        "from_qs_type": "list",
    }
