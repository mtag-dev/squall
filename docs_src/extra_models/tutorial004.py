from typing import List

from pydantic import Field, dataclasses
from squall import Squall

app = Squall()


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    description: str = Field(...)


items = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]


@app.get("/items/", response_model=List[Item])
async def read_items():
    return items
