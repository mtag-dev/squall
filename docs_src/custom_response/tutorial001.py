from squall import Squall
from squall.responses import UJSONResponse

app = Squall()


@app.get("/items/", response_class=UJSONResponse)
async def read_items():
    return [{"item_id": "Foo"}]
