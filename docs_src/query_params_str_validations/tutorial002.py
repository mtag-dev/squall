from typing import Optional

from squall import Query, Squall

app = Squall()


@app.get("/items/")
async def read_items(q: Optional[str] = Query(None, max_len=50)):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
