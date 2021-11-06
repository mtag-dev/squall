from typing import Optional

from squall import Header, Squall

app = Squall()


@app.get("/items/")
async def read_items(user_agent: Optional[str] = Header(None)):
    return {"User-Agent": user_agent}
