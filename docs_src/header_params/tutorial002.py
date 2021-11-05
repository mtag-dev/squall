from typing import Optional

from squall import Header, Squall

app = Squall()


@app.router.get("/items/")
async def read_items(
    strange_header: Optional[str] = Header(None, convert_underscores=False)
):
    return {"strange_header": strange_header}
