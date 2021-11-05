from squall import Squall

app = Squall()


@app.router.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.router.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
