from typing import Optional, Set

from pydantic import BaseModel
from squall import Squall

app = Squall()


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: Set[str] = []


@app.router.post("/items/", response_model=Item, tags=["items"])
async def create_item(item: Item):
    return item


@app.router.get("/items/", tags=["items"])
async def read_items():
    return [{"name": "Foo", "price": 42}]


@app.router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]
