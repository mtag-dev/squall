from typing import Optional

from pydantic import Field, dataclasses
from squall import Squall
from squall.responses import FileResponse


@dataclasses.dataclass()
class Item:
    id: str = Field(...)
    value: str = Field(...)


responses = {
    404: {"description": "Item not found"},
    302: {"description": "The item was moved"},
    403: {"description": "Not enough privileges"},
}


app = Squall()


@app.router.get(
    "/items/{item_id}",
    response_model=Item,
    responses={**responses, 200: {"content": {"image/png": {}}}},
)
async def read_item(item_id: str, img: Optional[bool] = None):
    if img:
        return FileResponse("image.png", media_type="image/png")
    else:
        return {"id": "foo", "value": "there goes my hero"}
