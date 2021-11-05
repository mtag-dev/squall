from squall import Squall

app = Squall()

items = {}


@app.on_event("startup")
async def startup_event():
    items["foo"] = {"name": "Fighters"}
    items["bar"] = {"name": "Tenders"}


@app.router.get("/items/{item_id}")
async def read_items(item_id: str):
    return items[item_id]
