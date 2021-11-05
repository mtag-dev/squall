from squall import Squall

app = Squall()


@app.router.get("/")
async def read_main():
    return {"msg": "Hello World"}
