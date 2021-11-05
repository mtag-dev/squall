from typing import List

from pydantic import BaseModel, HttpUrl
from squall import Squall

app = Squall()


class Image(BaseModel):
    url: HttpUrl
    name: str


@app.router.post("/images/multiple/")
async def create_multiple_images(images: List[Image]):
    return images
