from squall import Squall
from squall.responses import JSONResponse

app = Squall()


@app.router.get("/items/", response_class=JSONResponse)
async def read_items():
    return [{"item_id": "Foo"}]
