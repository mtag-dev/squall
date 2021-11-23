import typing
from dataclasses import dataclass, field
from decimal import Decimal

from squall.validators.head import Validator


@dataclass
class Request:
    path_params: typing.Dict[str, typing.Any] = field(default_factory=dict)
    query_params: typing.Dict[str, typing.Any] = field(default_factory=dict)
    headers: typing.Dict[str, typing.Any] = field(default_factory=dict)
    cookies: typing.Dict[str, typing.Any] = field(default_factory=dict)


def test_numeric_with_conversion():
    v = Validator(
        args=["request"],
        convertors={"int": int, "float": float, "decimal": Decimal},
    )
    v.add_rule("numeric", "path_params", "numeric1", gt=20, le=50, convert="decimal")
    v.add_rule("numeric", "path_params", "numeric2", gt=20, le=50, convert="int")
    v.add_rule("numeric", "path_params", "numeric3", gt=20, le=50, convert="float")
    validator = v.build()

    request = Request(path_params={"numeric1": 30, "numeric2": 30, "numeric3": 30})
    assert validator(request) == (
        {"numeric1": Decimal(30), "numeric2": 30, "numeric3": 30.0},
        [],
    )

    request = Request(path_params={"numeric1": 19, "numeric2": 19, "numeric3": 19})
    assert validator(request) == (
        {},
        [
            ("path_params", "numeric1", "Validation error", Decimal("19")),
            ("path_params", "numeric2", "Validation error", 19),
            ("path_params", "numeric3", "Validation error", 19.0),
        ],
    )

    request = Request(path_params={"numeric1": 51, "numeric2": 51, "numeric3": 51})
    assert validator(request) == (
        {},
        [
            ("path_params", "numeric1", "Validation error", Decimal("51")),
            ("path_params", "numeric2", "Validation error", 51),
            ("path_params", "numeric3", "Validation error", 51.0),
        ],
    )


def test_numeric_without_conversion():
    v = Validator(args=["request"], convertors={})
    v.add_rule("numeric", "path_params", "numeric1", gt=20, le=50)
    v.add_rule("numeric", "path_params", "numeric2", gt=20, le=50)
    v.add_rule("numeric", "path_params", "numeric3", gt=20, le=50)
    validator = v.build()

    request = Request(path_params={"numeric1": 30, "numeric2": 30, "numeric3": 30})
    assert validator(request) == ({"numeric1": 30, "numeric2": 30, "numeric3": 30}, [])

    request = Request(
        path_params={"numeric1": Decimal(30), "numeric2": 30.0, "numeric3": 30}
    )
    assert validator(request) == (
        {"numeric1": Decimal(30), "numeric2": 30.0, "numeric3": 30},
        [],
    )

    request = Request(path_params={"numeric1": 19, "numeric2": 19, "numeric3": 19})
    assert validator(request) == (
        {},
        [
            ("path_params", "numeric1", "Validation error", 19),
            ("path_params", "numeric2", "Validation error", 19),
            ("path_params", "numeric3", "Validation error", 19),
        ],
    )

    request = Request(path_params={"numeric1": 51, "numeric2": 51, "numeric3": 51})
    assert validator(request) == (
        {},
        [
            ("path_params", "numeric1", "Validation error", 51),
            ("path_params", "numeric2", "Validation error", 51),
            ("path_params", "numeric3", "Validation error", 51),
        ],
    )

    request = Request()
    assert validator(request) == (
        {},
        [
            ("path_params", "numeric1", "Mandatory field missed", Ellipsis),
            ("path_params", "numeric2", "Mandatory field missed", Ellipsis),
            ("path_params", "numeric3", "Mandatory field missed", Ellipsis),
        ],
    )


def test_strings():
    v = Validator(
        args=["request"],
        convertors={
            "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a),
            "bytes": lambda a: str(a).encode("utf-8") if type(a) != bytes else a,
        },
    )
    v.add_rule(
        "string", "path_params", "string1", min_length=3, max_length=5, convert="str"
    )
    v.add_rule(
        "string", "path_params", "string2", min_length=3, max_length=5, convert="bytes"
    )

    validator = v.build()
    request = Request(path_params={"string1": "303", "string2": "403"})
    assert validator(request) == ({"string1": "303", "string2": b"403"}, [])

    request = Request(path_params={"string1": 303, "string2": 403})
    assert validator(request) == ({"string1": "303", "string2": b"403"}, [])

    request = Request(path_params={"string1": "aa", "string2": "aaaaaa"})
    assert validator(request) == (
        {},
        [
            ("path_params", "string1", "Validation error", "aa"),
            ("path_params", "string2", "Validation error", b"aaaaaa"),
        ],
    )

    request = Request()
    assert validator(request) == (
        {},
        [
            ("path_params", "string1", "Mandatory field missed", Ellipsis),
            ("path_params", "string2", "Mandatory field missed", Ellipsis),
        ],
    )


def test_no_rules():
    v = Validator(args=["request"], convertors={})

    validator = v.build()
    request = Request(path_params={"put": "any", "noise": "here"})
    assert validator(request) == ({}, [])


def test_multiple_sources():
    v = Validator(args=["request"], convertors={})
    validator = v.build()
    request = Request(path_params={"put": "any"}, headers={"noise": "here"})
    assert validator(request) == ({}, [])

    v = Validator(args=["request"], convertors={"decimal": Decimal, "str": str})
    v.add_rule("numeric", "path_params", "numeric1", gt=20, le=50, convert="decimal")
    v.add_rule(
        "string", "headers", "string1", min_length=3, max_length=5, convert="str"
    )
    validator = v.build()

    request = Request(path_params={"numeric1": 20}, headers={"string1": "str"})
    assert validator(request) == (
        {"string1": "str"},
        [("path_params", "numeric1", "Validation error", Decimal("20"))],
    )


def test_default():
    v = Validator(args=["request"], convertors={})
    v.add_rule("numeric", "path_params", "numeric1", default=1)
    v.add_rule("string", "headers", "string1", default="default_str")
    validator = v.build()

    request = Request()
    assert validator(request) == ({"string1": "default_str", "numeric1": 1}, [])


def test_origin_key():
    v = Validator(args=["request"], convertors={})
    v.add_rule("numeric", "query_params", name="n1", key="numeric1")
    v.add_rule("numeric", "query_params", name="n2", key="numeric2")
    v.add_rule("numeric", "query_params", name="n3", key="numeric3")
    validator = v.build()

    request = Request(query_params={"numeric1": 30, "numeric2": 30, "numeric3": 30})
    assert validator(request) == ({"n1": 30, "n2": 30, "n3": 30}, [])


def test_lists():
    v = Validator(args=["request"], convertors={})
    v.add_rule(None, "query_params", "query1", as_list=True)
    validator = v.build()
    from starlette.datastructures import MultiDict

    qs = MultiDict()
    request = Request(query_params=qs)
    assert validator(request) == ({"query1": []}, [])

    v = Validator(args=["request"], convertors={"int": int})
    v.add_rule(None, "query_params", "query1", as_list=True)
    v.add_rule(None, "query_params", "query2", as_list=True)
    v.add_rule(None, "query_params", "query3", as_list=True, convert="int")
    validator = v.build()

    qs = MultiDict()
    qs.append("query1", "value1")
    qs.append("query2", "value1")
    qs.append("query2", "value2")
    qs.append("query3", "1")
    qs.append("query3", "2")
    request = Request(query_params=qs)
    assert validator(request) == (
        {"query1": ["value1"], "query2": ["value1", "value2"], "query3": [1, 2]},
        [],
    )
