from squall import Squall
from squall.testclient import TestClient

from .utils import needs_py39


@needs_py39
def test_typing():
    checks = [
        (list[int], [1, 2, 3]),
        (dict[str, list[int]], {"a": [1, 2, 3], "b": [4, 5, 6]}),
        (tuple[int, ...], [1, 2, 3]),
        (set[int], [1, 2, 3]),  # `set` is converted to `tuple`
    ]

    for test_type, expect in checks:
        app = Squall()

        @app.post("/", response_model=test_type)
        def post_endpoint():
            return expect

        res = TestClient(app).post("/", json=expect)
        assert res.status_code == 200, res.json()
        assert res.json() == expect
