from squall import Squall

app = Squall()


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
