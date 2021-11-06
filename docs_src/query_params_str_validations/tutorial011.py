from typing import List, Optional

from squall import Query, Squall

app = Squall()


@app.get("/items/")
async def read_items(q: Optional[List[str]] = Query(None)):
    return {"q": q}
