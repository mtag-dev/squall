from typing import List, Optional

from squall import Squall, Query

app = Squall()


@app.get("/items/")
async def read_items(q: Optional[List[str]] = Query(None)):
    query_items = {"q": q}
    return query_items
