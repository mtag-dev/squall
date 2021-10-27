from typing import Union

from pydantic import Field, dataclasses
from squall import Squall

app = Squall()


@dataclasses.dataclass
class BaseItem:
    description: str = Field(...)
    type: str = Field(...)


@dataclasses.dataclass
class CarItem(BaseItem):
    type = "car"


@dataclasses.dataclass
class PlaneItem(BaseItem):
    type = "plane"
    size: int = Field(...)


items = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


@app.get("/items/{item_id}", response_model=Union[PlaneItem, CarItem])
async def read_item(item_id: str):
    return items[item_id]
