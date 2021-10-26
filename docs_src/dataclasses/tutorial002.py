from dataclasses import dataclass, field
from typing import List, Optional

from squall import Squall


@dataclass
class Item:
    name: str
    price: float
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    tax: Optional[float] = None


app = Squall()


@app.get("/items/next", response_model=Item)
async def read_next_item():
    return {
        "name": "Island In The Moon",
        "price": 12.99,
        "description": "A place to be be playin' and havin' fun",
        "tags": ["breater"],
    }
