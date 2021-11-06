from squall import Squall
from squall.responses import RedirectResponse

app = Squall()


@app.get("/subdomain")
async def redirect_typer():
    return RedirectResponse("https://subdomain.example.com")
