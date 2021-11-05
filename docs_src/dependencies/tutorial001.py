from typing import Optional

from squall import Depends, Squall

app = Squall()


async def common_parameters(q: Optional[str] = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@app.router.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons


@app.router.get("/users/")
async def read_users(commons: dict = Depends(common_parameters)):
    return commons
