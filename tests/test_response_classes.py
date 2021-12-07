import pytest
from squall import Header, Squall
from squall.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
)
from squall.testclient import TestClient

app = Squall()

html_response = """
    <html>
        <head>
            <title>HTML</title>
        </head>
        <body>
            <h1>HTML!</h1>
        </body>
    </html>
"""


def fake_video_streamer():
    for _ in range(3):
        yield b"mandarinki"


@app.get("/json_response")
def get_json_response():
    return JSONResponse(content={"msg": "mandarinki"})


@app.get("/json_response_class", response_class=JSONResponse)
def get_json_response_class():
    return {"msg": "mandarinki"}


@app.get("/html_response")
def get_html_response():
    return HTMLResponse(content=html_response)


@app.get("/html_response_class", response_class=HTMLResponse)
def get_html_response_class():
    return html_response


@app.get("/plaintext_response")
def get_plaintext_response():
    return PlainTextResponse(content="mandarinki")


@app.get("/plaintext_response_class", response_class=PlainTextResponse)
def get_plaintext_response_class():
    return "mandarinki"


@app.get("/streaming_response")
def get_streaming_response():
    return StreamingResponse(content=fake_video_streamer())


@app.get("/streaming_response_class", response_class=StreamingResponse)
def get_streaming_response_class():
    return fake_video_streamer()


@app.get("/file_response")
def get_file_response(response_file: str = Header()):
    return FileResponse(response_file)


@app.get("/file_response_class", response_class=FileResponse)
def get_file_response_class(response_file: str = Header()):
    return response_file


@app.get("/redirect_response")
def get_redirect_response():
    return RedirectResponse("https://mandarinki.com")


@app.get("/redirect_response_class", response_class=RedirectResponse)
def get_redirect_response_class():
    return "https://mandarinki.com"


client = TestClient(app)


@pytest.mark.parametrize("path", ["/json_response", "/json_response_class"])
def test_json_response(path):
    with client:
        response = client.get(path)
    assert response.json() == {"msg": "mandarinki"}
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize("path", ["/html_response", "/html_response_class"])
def test_html_response(path):
    with client:
        response = client.get(path)
    assert response.content.decode() == html_response
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("path", ["/plaintext_response", "/plaintext_response_class"])
def test_plaintext_response(path):
    with client:
        response = client.get(path)
    assert response.content.decode() == "mandarinki"
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.parametrize("path", ["/streaming_response", "/streaming_response_class"])
def test_streaming_response(path):
    with client:
        response = client.get(path)
    assert response.content.decode() == "mandarinki" * 3


@pytest.mark.parametrize("path", ["/file_response", "/file_response_class"])
def test_file_response(path, response_file):
    with client:
        response = client.get(path, headers={"response_file": str(response_file)})
    assert response.content == b"salokovbasasaltison"
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.parametrize("path", ["/redirect_response", "/redirect_response_class"])
def test_redirect_response(path):
    with client:
        response = client.get(path, allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://mandarinki.com"
