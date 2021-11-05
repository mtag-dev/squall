from typing import List, Optional

import pytest
from pydantic import ValidationError
from pydantic.dataclasses import dataclass
from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class Item:
    name: str
    price: Optional[float] = None
    owner_ids: Optional[List[int]] = None


@app.router.get("/items/invalid", response_model=Item)
def get_invalid():
    return {"name": "invalid", "price": "foo"}


@app.router.get("/items/innerinvalid", response_model=Item)
def get_innerinvalid():
    return {"name": "double invalid", "price": "foo", "owner_ids": ["foo", "bar"]}


@app.router.get("/items/invalidlist", response_model=List[Item])
def get_invalidlist():
    return [
        {"name": "foo"},
        {"name": "bar", "price": "bar"},
        {"name": "baz", "price": "baz"},
    ]


client = TestClient(app)


def test_invalid():
    with pytest.raises(ValidationError):
        client.get("/items/invalid")


def test_double_invalid():
    with pytest.raises(ValidationError):
        client.get("/items/innerinvalid")


def test_invalid_list():
    with pytest.raises(ValidationError):
        client.get("/items/invalidlist")
