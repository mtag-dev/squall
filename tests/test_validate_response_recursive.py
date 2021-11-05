from typing import List

from pydantic import Field, dataclasses
from squall import Squall
from squall.testclient import TestClient

app = Squall()


@dataclasses.dataclass
class RecursiveItem:
    sub_items: List["RecursiveItem"] = Field(default_factory=list)
    name: str = Field(...)


RecursiveItem.__pydantic_model__.update_forward_refs()


@dataclasses.dataclass
class RecursiveSubitemInSubmodel:
    sub_items2: List["RecursiveItemViaSubmodel"] = Field(default_factory=list)
    name: str = Field(...)


@dataclasses.dataclass
class RecursiveItemViaSubmodel:
    sub_items1: List[RecursiveSubitemInSubmodel] = Field(default_factory=list)
    name: str = Field(...)


RecursiveSubitemInSubmodel.__pydantic_model__.update_forward_refs()


@app.router.get("/items/recursive", response_model=RecursiveItem)
def get_recursive():
    return {"name": "item", "sub_items": [{"name": "subitem", "sub_items": []}]}


@app.router.get("/items/recursive-submodel", response_model=RecursiveItemViaSubmodel)
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
