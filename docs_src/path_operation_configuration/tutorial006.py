from squall import Squall

app = Squall()


@app.router.get("/items/", tags=["items"])
async def read_items():
    return [{"name": "Foo", "price": 42}]


@app.router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]


@app.router.get("/elements/", tags=["items"], deprecated=True)
async def read_elements():
    return [{"item_id": "Foo"}]
