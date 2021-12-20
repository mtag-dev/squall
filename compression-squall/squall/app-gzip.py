from squall import Squall
from squall.compression import Compression
import orjson

app = Squall(compression=Compression())

with open('sprint-response.json') as file:
    response_data = orjson.loads(file.read())


@app.get("/squall_compression")
async def raw_sprint():
    return response_data
