from typing import List

from pydantic import BaseModel, HttpUrl
from squall import Squall

app = Squall()


class Image(BaseModel):
    url: HttpUrl
    name: str


@app.post("/images/multiple/")
async def create_multiple_images(images: List[Image]):
    return images
