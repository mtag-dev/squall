import pytest

from squall import APIRouter, Squall
from squall.testclient import TestClient

app = Squall()

router = APIRouter()


@router.get("")
def get_empty():
    return ["OK"]


app.include_router(router, prefix="/prefix")


client = TestClient(app)


def test_use_empty():
    with client:
        response = client.get("/prefix")
        assert response.status_code == 200, response.text
        assert response.json() == ["OK"]

        response = client.get("/prefix/")
        assert response.status_code == 200, response.text
        assert response.json() == ["OK"]


def test_include_empty():
    # if both include and router.path are empty - it should raise exception
    with pytest.raises(Exception):
        app.include_router(router)
