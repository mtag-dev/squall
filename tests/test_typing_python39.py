import pytest
from squall import Squall
from squall.testclient import TestClient

from .utils import needs_py39


@needs_py39
@pytest.mark.parametrize(
    "test_type,expect",
    [
        (list[int], [1, 2, 3]),
        (dict[str, list[int]], {"a": [1, 2, 3], "b": [4, 5, 6]}),
        (tuple[int, ...], [1, 2, 3]),
        (set[int], [1, 2, 3]),  # `set` is converted to `tuple`
    ],
)
def test_typing(test_type, expect):
    app = Squall()

    @app.post("/", response_model=test_type)
    def post_endpoint(input: test_type):
        return input

    res = TestClient(app).post("/", json=expect)
    assert res.status_code == 200, res.json()
    assert res.json() == expect
