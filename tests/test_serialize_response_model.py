from typing import Dict, List, Optional

from pydantic import Field, dataclasses
from squall import Squall
from starlette.testclient import TestClient

app = Squall()


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    price: Optional[float] = None
    owner_ids: Optional[List[int]] = None


@app.router.get("/items/valid", response_model=Item)
def get_valid():
    return Item(name="valid", price=1.0)


@app.router.get("/items/coerce", response_model=Item)
def get_coerce():
    return Item(name="coerce", price="1.0")


@app.router.get("/items/validlist", response_model=List[Item])
def get_validlist():
    return [
        Item(name="foo"),
        Item(name="bar", price=1.0),
        Item(name="baz", price=2.0, owner_ids=[1, 2, 3]),
    ]


@app.router.get("/items/validdict", response_model=Dict[str, Item])
def get_validdict():
    return {
        "k1": Item(name="foo"),
        "k2": Item(name="bar", price=1.0),
        "k3": Item(name="baz", price=2.0, owner_ids=[1, 2, 3]),
    }


client = TestClient(app)


def test_valid():
    response = client.get("/items/valid")
    response.raise_for_status()
    assert response.json() == {"name": "valid", "price": 1.0, "owner_ids": None}


def test_coerce():
    response = client.get("/items/coerce")
    response.raise_for_status()
    assert response.json() == {
        "name": "coerce",
        "price": 1.0,
        "owner_ids": None,
    }


def test_validlist():
    response = client.get("/items/validlist")
    response.raise_for_status()
    assert response.json() == [
        {"name": "foo", "price": None, "owner_ids": None},
        {"name": "bar", "price": 1.0, "owner_ids": None},
        {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]


def test_validdict():
    response = client.get("/items/validdict")
    response.raise_for_status()
    assert response.json() == {
        "k1": {"name": "foo", "price": None, "owner_ids": None},
        "k2": {"name": "bar", "price": 1.0, "owner_ids": None},
        "k3": {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    }
