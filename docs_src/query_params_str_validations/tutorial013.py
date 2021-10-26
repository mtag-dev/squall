from squall import Squall, Query

app = Squall()


@app.get("/items/")
async def read_items(q: list = Query([])):
    query_items = {"q": q}
    return query_items
