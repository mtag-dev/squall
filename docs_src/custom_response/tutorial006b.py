from squall import Squall
from squall.responses import RedirectResponse

app = Squall()


@app.get("/squall", response_class=RedirectResponse)
async def redirect_squall():
    return "https://squall.mtag.dev"
