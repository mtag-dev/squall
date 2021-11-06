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


@app.put("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}
