from squall import Squall
from squall.responses import RedirectResponse

app = Squall()


@app.router.get("/pydantic", response_class=RedirectResponse, status_code=302)
async def redirect_pydantic():
    return "https://pydantic-docs.helpmanual.io/"
