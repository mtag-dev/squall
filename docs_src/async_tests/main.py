from squall import Squall

app = Squall()


@app.router.get("/")
async def root():
    return {"message": "Tomato"}
