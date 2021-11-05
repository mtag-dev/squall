from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from squall import Squall
from squall.encoders import jsonable_encoder

fake_db = {}


class Item(BaseModel):
    title: str
    timestamp: datetime
    description: Optional[str] = None


app = Squall()


@app.router.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    fake_db[id] = json_compatible_item_data
