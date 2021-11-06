from typing import Optional

from squall import Cookie, Squall

app = Squall()


@app.get("/items/")
async def read_items(ads_id: Optional[str] = Cookie(None)):
    return {"ads_id": ads_id}
