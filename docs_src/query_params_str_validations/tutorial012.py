from typing import List

from squall import Query, Squall

app = Squall()


@app.get("/items/")
async def read_items(q: List[str] = Query(["foo", "bar"])):
    query_items = {"q": q}
    return query_items
