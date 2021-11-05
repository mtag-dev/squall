from typing import List

import yaml
from pydantic import Field, ValidationError, dataclasses
from squall import HTTPException, Request, Squall

app = Squall()


@dataclasses.dataclass
class Item:
    name: str = Field(...)
    tags: List[str] = Field(...)


@app.router.post(
    "/items/",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/x-yaml": {"schema": Item.__pydantic_model__.schema()}
            },
            "required": True,
        },
    },
)
async def create_item(request: Request):
    raw_body = await request.body()
    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        raise HTTPException(status_code=422, detail="Invalid YAML")
    try:
        item = Item(**data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    return item
