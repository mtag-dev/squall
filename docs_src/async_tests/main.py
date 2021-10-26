from squall import Squall

app = Squall()


@app.get("/")
async def root():
    return {"message": "Tomato"}
