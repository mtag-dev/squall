from squall import Squall
from squall.middleware.httpsredirect import HTTPSRedirectMiddleware

app = Squall()

app.add_middleware(HTTPSRedirectMiddleware)


@app.get("/")
async def main():
    return {"message": "Hello World"}
