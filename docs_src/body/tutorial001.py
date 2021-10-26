from typing import Optional

from pydantic import BaseModel
from squall import Squall


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


app = Squall()


@app.post("/items/")
async def create_item(item: Item):
    return item
