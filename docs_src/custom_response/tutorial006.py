from squall import Squall
from squall.responses import RedirectResponse

app = Squall()


@app.router.get("/subdomain")
async def redirect_typer():
    return RedirectResponse("https://subdomain.example.com")
