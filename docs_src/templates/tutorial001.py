from squall import Squall, Request
from squall.responses import HTMLResponse
from squall.staticfiles import StaticFiles
from squall.templating import Jinja2Templates

app = Squall()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})
