from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from squall import Squall
from squall.encoders import jsonable_encoder
from squall.responses import JSONResponse


class Item(BaseModel):
    title: str
    timestamp: datetime
    description: Optional[str] = None


app = Squall()


@app.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)
