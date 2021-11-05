from typing import Dict

from squall import Squall

app = Squall()


@app.router.get("/keyword-weights/", response_model=Dict[str, float])
async def read_keyword_weights():
    return {"foo": 2.3, "bar": 3.4}
