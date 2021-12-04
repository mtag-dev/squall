from dataclasses import dataclass, field
from typing import List

from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclass
class RecursiveItem:
    name: str = field()
    sub_items: List["RecursiveItem"] = field(default_factory=list)


@dataclass
class RecursiveSubitemInSubmodel:
    name: str = field()
    sub_items2: List["RecursiveItemViaSubmodel"] = field(default_factory=list)


@dataclass
class RecursiveItemViaSubmodel:
    name: str = field()
    sub_items1: List[RecursiveSubitemInSubmodel] = field(default_factory=list)


@app.get("/items/recursive", response_model=RecursiveItem)
def get_recursive():
    return {"name": "item", "sub_items": [{"name": "subitem", "sub_items": []}]}


@app.get("/items/recursive-submodel", response_model=RecursiveItemViaSubmodel)
def get_recursive_submodel():
    return {
        "name": "item",
        "sub_items1": [
            {
                "name": "subitem",
                "sub_items2": [
                    {
                        "name": "subsubitem",
                        "sub_items1": [{"name": "subsubsubitem", "sub_items2": []}],
                    }
                ],
            }
        ],
    }


client = TestClient(app)


def test_recursive():
    response = client.get("/items/recursive")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "sub_items": [{"name": "subitem", "sub_items": []}],
        "name": "item",
    }

    response = client.get("/items/recursive-submodel")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "name": "item",
        "sub_items1": [
            {
                "name": "subitem",
                "sub_items2": [
                    {
                        "name": "subsubitem",
                        "sub_items1": [{"name": "subsubsubitem", "sub_items2": []}],
                    }
                ],
            }
        ],
    }
