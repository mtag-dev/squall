from squall import Squall
from squall.middleware.gzip import GZipMiddleware

app = Squall()

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.router.get("/")
async def main():
    return "somebigcontent"
