from squall import Squall

app = Squall()


@app.router.get("/items/", include_in_schema=False)
async def read_items():
    return [{"item_id": "Foo"}]
