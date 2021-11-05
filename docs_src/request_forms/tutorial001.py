from squall import Form, Squall

app = Squall()


@app.router.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
