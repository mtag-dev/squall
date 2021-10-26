from squall import Squall, Form

app = Squall()


@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
