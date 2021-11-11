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
        {"numeric1": Decimal("19"), "numeric2": 19, "numeric3": 19.0},
        [
            ("numeric1", "Validation error"),
            ("numeric2", "Validation error"),
            ("numeric3", "Validation error"),
        ],
    )

    param = {"numeric1": 51, "numeric2": 51, "numeric3": 51}
    assert validator(param) == (
        {"numeric1": 51, "numeric2": 51, "numeric3": 51},
        [
            ("numeric1", "Validation error"),
            ("numeric2", "Validation error"),
            ("numeric3", "Validation error"),
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
        {"numeric1": 19, "numeric2": 19, "numeric3": 19},
        [
            ("numeric1", "Validation error"),
            ("numeric2", "Validation error"),
            ("numeric3", "Validation error"),
        ],
    )

    param = {"numeric1": 51, "numeric2": 51, "numeric3": 51}
    assert validator(param) == (
        {"numeric1": 51, "numeric2": 51, "numeric3": 51},
        [
            ("numeric1", "Validation error"),
            ("numeric2", "Validation error"),
            ("numeric3", "Validation error"),
        ],
    )

    param = {}
    assert validator(param) == (
        {"numeric1": None, "numeric2": None, "numeric3": None},
        [
            ("numeric1", "Can't be None"),
            ("numeric2", "Can't be None"),
            ("numeric3", "Can't be None"),
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
        {"string1": "aa", "string2": b"aaaaaa"},
        [
            ("string1", "Validation error"),
            ("string2", "Validation error"),
        ],
    )

    param = {}
    assert validator(param) == (
        {"string1": None, "string2": None},
        [("string1", "Can't be None"), ("string2", "Can't be None")],
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
        {"numeric1": Decimal("20"), "string1": "str"},
        [("numeric1", "Validation error")],
    )
