import pytest
from squall.validators.inputs import Validator


def test_sample():
    v = Validator(
        args=["param"],
        convertors={
            "int": int,
            "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a),
        },
    )
    v.add_rule("numeric", "param", "orders", name="my_orders", gt=20)
    v.add_rule(
        "string",
        "param",
        "items",
        min_length=3,
        max_length=5,
        default="anon",
        convert="str",
    )
    validator = v.build()
    param = {"orders": 30, "items": b"403", "useles1": 1, "useles2": 40}
    assert validator(param) == ({'my_orders': 30, 'items': '403'}, [])
    param = {"orders": 20, "useles1": 1, "useles2": 40}
    assert validator(param) == ({'items': 'anon'}, [('param', 'orders', 'Validation error')])
