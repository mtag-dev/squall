from pydantic import Field, dataclasses
from squall import Squall
from squall.responses import JSONResponse


@dataclasses.dataclass
class Item:
    id: str = Field(...)
    value: str = Field(...)


@dataclasses.dataclass
class Message:
    message: str = Field(...)


app = Squall()


@app.get("/items/{item_id}", response_model=Item, responses={404: {"model": Message}})
async def read_item(item_id: str):
    if item_id == "foo":
        return {"id": "foo", "value": "there goes my hero"}
    else:
        return JSONResponse(status_code=404, content={"message": "Item not found"})
