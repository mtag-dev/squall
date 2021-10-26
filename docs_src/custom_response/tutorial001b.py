from squall import Squall
from squall.responses import ORJSONResponse

app = Squall()


@app.get("/items/", response_class=ORJSONResponse)
async def read_items():
    return [{"item_id": "Foo"}]
