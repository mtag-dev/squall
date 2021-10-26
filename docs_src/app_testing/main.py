from squall import Squall

app = Squall()


@app.get("/")
async def read_main():
    return {"msg": "Hello World"}
