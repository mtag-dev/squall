from squall import Depends, Squall

from .dependencies import get_query_token, get_token_header
from .internal import admin
from .routers import items, users

app = Squall(dependencies=[Depends(get_query_token)])


app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)


@app.router.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
