from typing import Optional

from pydantic import Field, dataclasses
from squall import Squall
from squall.responses import FileResponse


@dataclasses.dataclass
class Item:
    id: str = Field(...)
    value: str = Field(...)


app = Squall()


@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Return the JSON item or an image.",
        }
    },
)
async def read_item(item_id: str, img: Optional[bool] = None):
    if img:
        return FileResponse("image.png", media_type="image/png")
    else:
        return {"id": "foo", "value": "there goes my hero"}
