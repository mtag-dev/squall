from decimal import Decimal

from squall.validators.inputs import Validator


def test_numeric_with_conversion():
    v = Validator(
        args=["param"],
        convertors={"int": int, "float": float, "decimal": Decimal},
    )
    v.add_rule("numeric", "param", "numeric1", gt=20, le=50, convert="decimal")
    v.add_rule("numeric", "param", "numeric2", gt=20, le=50, convert="int")
    v.add_rule("numeric", "param", "numeric3", gt=20, le=50, convert="float")
    validator = v.build()

    param = {"numeric1": 30, "numeric2": 30, "numeric3": 30}
    assert validator(param) == (
        {"numeric1": Decimal(30), "numeric2": 30, "numeric3": 30.0},
        [],
    )

    param = {"numeric1": 19, "numeric2": 19, "numeric3": 19}
    assert validator(param) == (
        {},
        [
            ("param", "numeric1", "Validation error"),
            ("param", "numeric2", "Validation error"),
            ("param", "numeric3", "Validation error"),
        ],
    )

    param = {"numeric1": 51, "numeric2": 51, "numeric3": 51}
    assert validator(param) == (
        {},
        [
            ("param", "numeric1", "Validation error"),
            ("param", "numeric2", "Validation error"),
            ("param", "numeric3", "Validation error"),
        ],
    )


def test_numeric_without_conversion():
    v = Validator(args=["param"], convertors={})
    v.add_rule("numeric", "param", "numeric1", gt=20, le=50)
    v.add_rule("numeric", "param", "numeric2", gt=20, le=50)
    v.add_rule("numeric", "param", "numeric3", gt=20, le=50)
    validator = v.build()

    param = {"numeric1": 30, "numeric2": 30, "numeric3": 30}
    assert validator(param) == ({"numeric1": 30, "numeric2": 30, "numeric3": 30}, [])

    param = {"numeric1": Decimal(30), "numeric2": 30.0, "numeric3": 30}
    assert validator(param) == (
        {"numeric1": Decimal(30), "numeric2": 30.0, "numeric3": 30},
        [],
    )

    param = {"numeric1": 19, "numeric2": 19, "numeric3": 19}
    assert validator(param) == (
        {},
        [
            ("param", "numeric1", "Validation error"),
            ("param", "numeric2", "Validation error"),
            ("param", "numeric3", "Validation error"),
        ],
    )

    param = {"numeric1": 51, "numeric2": 51, "numeric3": 51}
    assert validator(param) == (
        {},
        [
            ("param", "numeric1", "Validation error"),
            ("param", "numeric2", "Validation error"),
            ("param", "numeric3", "Validation error"),
        ],
    )

    param = {}
    assert validator(param) == (
        {},
        [
            ("param", "numeric1", "Can't be None"),
            ("param", "numeric2", "Can't be None"),
            ("param", "numeric3", "Can't be None"),
        ],
    )


def test_strings():
    v = Validator(
        args=["param"],
        convertors={
            "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a),
            "bytes": lambda a: str(a).encode("utf-8") if type(a) != bytes else a,
        },
    )
    v.add_rule("string", "param", "string1", min_length=3, max_length=5, convert="str")
    v.add_rule(
        "string", "param", "string2", min_length=3, max_length=5, convert="bytes"
    )

    validator = v.build()
    param = {"string1": "303", "string2": "403"}
    assert validator(param) == ({"string1": "303", "string2": b"403"}, [])

    param = {"string1": 303, "string2": 403}
    assert validator(param) == ({"string1": "303", "string2": b"403"}, [])

    param = {"string1": "aa", "string2": "aaaaaa"}
    assert validator(param) == (
        {},
        [
            ("param", "string1", "Validation error"),
            ("param", "string2", "Validation error"),
        ],
    )

    param = {}
    assert validator(param) == (
        {},
        [("param", "string1", "Can't be None"), ("param", "string2", "Can't be None")],
    )


def test_no_rules():
    v = Validator(args=["param"], convertors={})

    validator = v.build()
    param = {"put": "any", "noise": "here"}
    assert validator(param) == ({}, [])


def test_multiple_sources():
    v = Validator(args=["param", "header"], convertors={})
    validator = v.build()
    param = {"put": "any"}
    header = {"noise": "here"}
    assert validator(param, header) == ({}, [])

    v = Validator(args=["param", "header"], convertors={"decimal": Decimal, "str": str})
    v.add_rule("numeric", "param", "numeric1", gt=20, le=50, convert="decimal")
    v.add_rule("string", "header", "string1", min_length=3, max_length=5, convert="str")
    validator = v.build()
    param = {"numeric1": 20}
    header = {"string1": "str"}
    assert validator(param, header) == (
        {"string1": "str"},
        [("param", "numeric1", "Validation error")],
    )
