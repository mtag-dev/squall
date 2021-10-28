from typing import Optional

from pydantic import Field, dataclasses
from squall import Squall


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    description: Optional[str] = None
    price: float = Field(...)
    tax: Optional[float] = None


app = Squall()


@app.post("/items/")
async def create_item(item: Item):
    return item
