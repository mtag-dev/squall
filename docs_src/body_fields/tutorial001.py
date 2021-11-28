from typing import Optional

from pydantic import Field, dataclasses
from squall import Body, Squall

app = Squall()


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    description: Optional[str] = Field(
        None, title="The description of the item", max_len=300
    )
    price: float = Field(..., gt=0, description="The price must be greater than zero")
    tax: Optional[float] = None


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item = Body(..., embed=True)):
    results = {"item_id": item_id, "item": item}
    return results
