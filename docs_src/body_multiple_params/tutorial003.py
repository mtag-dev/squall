from typing import Optional

from pydantic import Field, dataclasses
from squall import Body, Squall

app = Squall()


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    description: Optional[str] = None
    price: float = Field(...)
    tax: Optional[float] = None


@dataclasses.dataclass
class User:
    username: str = Field(...)
    full_name: Optional[str] = None


@app.router.put("/items/{item_id}")
async def update_item(
    item_id: int, item: Item, user: User, importance: int = Body(...)
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results
