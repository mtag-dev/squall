from squall import Squall
from squall.responses import PlainTextResponse

app = Squall()


@app.router.get("/", response_class=PlainTextResponse)
async def main():
    return "Hello World"
