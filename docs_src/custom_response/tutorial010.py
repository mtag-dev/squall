from squall import Squall
from squall.responses import ORJSONResponse

app = Squall(default_response_class=ORJSONResponse)


@app.router.get("/items/")
async def read_items():
    return [{"item_id": "Foo"}]
