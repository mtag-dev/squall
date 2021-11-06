from dataclasses import dataclass
from typing import Optional

from squall import Squall


@dataclass
class Item:
    name: str
    price: float
    description: Optional[str] = None
    tax: Optional[float] = None


app = Squall()


@app.post("/items/")
async def create_item(item: Item):
    return item
