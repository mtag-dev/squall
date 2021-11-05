from squall import Squall

app = Squall(docs_url="/documentation", redoc_url=None)


@app.router.get("/items/")
async def read_items():
    return [{"name": "Foo"}]
