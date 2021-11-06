from squall import Squall

app = Squall()


@app.post("/items/", status_code=201)
async def create_item(name: str):
    return {"name": name}
