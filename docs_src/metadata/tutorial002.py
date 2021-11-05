from squall import Squall

app = Squall(openapi_url="/api/v1/openapi.json")


@app.router.get("/items/")
async def read_items():
    return [{"name": "Foo"}]
