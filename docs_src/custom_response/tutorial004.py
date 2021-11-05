from squall import Squall
from squall.responses import HTMLResponse

app = Squall()


def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.router.get("/items/", response_class=HTMLResponse)
async def read_items():
    return generate_html_response()
