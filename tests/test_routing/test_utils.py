from typing import Optional

from squall.params import Cookie, Header, Num, Param, Query, Str
from squall.routing_.utils import get_handler_head_params


def test_get_handler_args_no_args():
    def handler():
        pass

    assert get_handler_head_params(handler) == []


def test_get_handler_args_no_annotation():
    def handler(a, b=Query(...), c=Param(...), d=Header(...), e=Cookie(...)):
        pass

    common = {}
    assert get_handler_head_params(handler) == [
        {"name": "a", "source": "param"},
        {"name": "b", "source": "query", **common},
        {"name": "c", "source": "param", **common},
        {"name": "d", "source": "header", **common},
        {"name": "e", "source": "cookie", **common},
    ]


def test_get_handler_args_origin():
    def handler(
        b=Query(..., origin="from_b"),
        c=Param(..., origin="from_c"),
        d=Header(..., origin="from_d"),
        e=Cookie(..., origin="from_e"),
    ):
        pass

    common = {}
    assert get_handler_head_params(handler) == [
        {"name": "b", "source": "query", "origin": "from_b", **common},
        {"name": "c", "source": "param", "origin": "from_c", **common},
        {"name": "d", "source": "header", "origin": "from_d", **common},
        {"name": "e", "source": "cookie", "origin": "from_e", **common},
    ]


def test_get_handler_args_annotations():
    def handler(b: int, c: str, d: bytes, e: float):
        pass

    assert get_handler_head_params(handler) == [
        {"name": "b", "source": "param", "validate": "numeric", "convert": "int"},
        {"name": "c", "source": "param", "validate": "string", "convert": "str"},
        {"name": "d", "source": "param", "validate": "string", "convert": "bytes"},
        {"name": "e", "source": "param", "validate": "numeric", "convert": "float"},
    ]


def test_get_handler_args_direct_defaults():
    def handler(
        a: Optional[str] = None,
        b: int = 1,
        c: str = "Hey",
        d: bytes = b"Hey",
        e: float = 3.14,
    ):
        pass

    assert get_handler_head_params(handler) == [
        {
            "name": "a",
            "source": "param",
            "convert": "str",
            "validate": "string",
            "default": None,
            "optional": True,
        },
        {
            "name": "b",
            "source": "param",
            "validate": "numeric",
            "convert": "int",
            "default": 1,
        },
        {
            "name": "c",
            "source": "param",
            "validate": "string",
            "convert": "str",
            "default": "Hey",
        },
        {
            "name": "d",
            "source": "param",
            "validate": "string",
            "convert": "bytes",
            "default": b"Hey",
        },
        {
            "name": "e",
            "source": "param",
            "validate": "numeric",
            "convert": "float",
            "default": 3.14,
        },
    ]


def test_get_handler_args_assigned_instance_defaults():
    def handler(
        a: Optional[str] = Param(None),
        b: int = Param(1),
        c: str = Query("Hey"),
        d: bytes = Header(b"Hey"),
        e: float = Cookie(3.14),
    ):
        pass

    assert get_handler_head_params(handler) == [
        {
            "name": "a",
            "source": "param",
            "validate": "string",
            "convert": "str",
            "default": None,
            "optional": True,
        },
        {
            "name": "b",
            "source": "param",
            "validate": "numeric",
            "convert": "int",
            "default": 1,
        },
        {
            "name": "c",
            "source": "query",
            "validate": "string",
            "convert": "str",
            "default": "Hey",
        },
        {
            "name": "d",
            "source": "header",
            "validate": "string",
            "convert": "bytes",
            "default": b"Hey",
        },
        {
            "name": "e",
            "source": "cookie",
            "validate": "numeric",
            "convert": "float",
            "default": 3.14,
        },
    ]


def test_get_handler_args_validation_parameters():
    def handler(
        a: Optional[str] = Param(None, valid=Str(min_length=2)),
        b: int = Param(1, valid=Num(ge=1, le=2)),
        c: str = Query("Hey", valid=Str(min_length=2, max_length=5)),
        d: bytes = Header(b"Hey", valid=Str(min_length=2, max_length=5)),
        e: float = Cookie(3.14, valid=Num(ge=3.14, le=3.15)),
    ):
        pass

    assert get_handler_head_params(handler) == [
        {
            "name": "a",
            "source": "param",
            "convert": "str",
            "default": None,
            "optional": True,
            "validate": "string",
            "min_length": 2,
        },
        {
            "name": "b",
            "source": "param",
            "convert": "int",
            "default": 1,
            "ge": 1,
            "le": 2,
            "validate": "numeric",
        },
        {
            "name": "c",
            "source": "query",
            "convert": "str",
            "default": "Hey",
            "validate": "string",
            "min_length": 2,
            "max_length": 5,
        },
        {
            "name": "d",
            "source": "header",
            "convert": "bytes",
            "default": b"Hey",
            "validate": "string",
            "min_length": 2,
            "max_length": 5,
        },
        {
            "name": "e",
            "source": "cookie",
            "convert": "float",
            "default": 3.14,
            "ge": 3.14,
            "le": 3.15,
            "validate": "numeric",
        },
    ]
