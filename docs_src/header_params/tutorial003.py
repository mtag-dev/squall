from typing import List, Optional

from squall import Header, Squall

app = Squall()


@app.router.get("/items/")
async def read_items(x_token: Optional[List[str]] = Header(None)):
    return {"X-Token values": x_token}
