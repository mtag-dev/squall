from typing import Optional

from squall.params import Cookie, Header, Param, Query
from squall.routing_.utils import get_handler_args


def test_get_handler_args_no_args():
    def handler():
        pass

    assert get_handler_args(handler) == []


def test_get_handler_args_no_annotation():
    def handler(a, b=Query(...), c=Param(...), d=Header(...), e=Cookie(...)):
        pass

    common = {}
    assert get_handler_args(handler) == [
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
    assert get_handler_args(handler) == [
        {"name": "b", "source": "query", "origin": "from_b", **common},
        {"name": "c", "source": "param", "origin": "from_c", **common},
        {"name": "d", "source": "header", "origin": "from_d", **common},
        {"name": "e", "source": "cookie", "origin": "from_e", **common},
    ]


def test_get_handler_args_annotations():
    def handler(b: int, c: str, d: bytes, e: float):
        pass

    common = {}
    assert get_handler_args(handler) == [
        {"name": "b", "source": "param", "convert": "int", **common},
        {"name": "c", "source": "param", "convert": "str", **common},
        {"name": "d", "source": "param", "convert": "bytes", **common},
        {"name": "e", "source": "param", "convert": "float", **common},
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

    assert get_handler_args(handler) == [
        {
            "name": "a",
            "source": "param",
            "convert": "str",
            "default": None,
            "optional": True,
        },
        {"name": "b", "source": "param", "convert": "int", "default": 1},
        {"name": "c", "source": "param", "convert": "str", "default": "Hey"},
        {"name": "d", "source": "param", "convert": "bytes", "default": b"Hey"},
        {"name": "e", "source": "param", "convert": "float", "default": 3.14},
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

    assert get_handler_args(handler) == [
        {
            "name": "a",
            "source": "param",
            "convert": "str",
            "default": None,
            "optional": True,
        },
        {"name": "b", "source": "param", "convert": "int", "default": 1},
        {"name": "c", "source": "query", "convert": "str", "default": "Hey"},
        {"name": "d", "source": "header", "convert": "bytes", "default": b"Hey"},
        {"name": "e", "source": "cookie", "convert": "float", "default": 3.14},
    ]


def test_get_handler_args_validation_parameters():
    def handler(
        a: Optional[str] = Param(None),
        b: int = Param(1),
        c: str = Query("Hey"),
        d: bytes = Header(b"Hey"),
        e: float = Cookie(3.14),
    ):
        pass

    assert get_handler_args(handler) == [
        {
            "name": "a",
            "source": "param",
            "convert": "str",
            "default": None,
            "optional": True,
        },
        {"name": "b", "source": "param", "convert": "int", "default": 1},
        {"name": "c", "source": "query", "convert": "str", "default": "Hey"},
        {"name": "d", "source": "header", "convert": "bytes", "default": b"Hey"},
        {"name": "e", "source": "cookie", "convert": "float", "default": 3.14},
    ]
