from squall import Squall
from squall.responses import PlainTextResponse

app = Squall()


@app.get("/", response_class=PlainTextResponse)
async def main():
    return "Hello World"
