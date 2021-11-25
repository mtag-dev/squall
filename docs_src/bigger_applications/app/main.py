# from squall import Depends, Squall
#
# from .dependencies import get_query_token
# from .internal import admin
# from .routers import items, users
#
# app = Squall(dependencies=[Depends(get_query_token)])
#
#
# app.include_router(users.router)
# app.include_router(items.router)
# app.include_router(admin.router)
#
#
# @app.get("/")
# async def root():
#     return {"message": "Hello Bigger Applications!"}
