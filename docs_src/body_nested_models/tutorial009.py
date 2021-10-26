from typing import Dict

from squall import Squall

app = Squall()


@app.post("/index-weights/")
async def create_index_weights(weights: Dict[int, float]):
    return weights
