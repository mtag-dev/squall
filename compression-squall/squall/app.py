from squall import Squall
import orjson

app = Squall()

with open('sprint-response.json') as file:
    response_data = orjson.loads(file.read())


@app.get("/nginx_compression")
async def raw_sprint():
    return response_data
