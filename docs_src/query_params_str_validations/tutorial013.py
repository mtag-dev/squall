from squall import Query, Squall

app = Squall()


@app.router.get("/items/")
async def read_items(q: list = Query([])):
    query_items = {"q": q}
    return query_items
