from squall import Form, Squall
from squall.testclient import TestClient

app = Squall()


@app.router.post("/form/python-list")
def post_form_param_list(items: list = Form(...)):
    return items


@app.router.post("/form/python-set")
def post_form_param_set(items: set = Form(...)):
    return items


@app.router.post("/form/python-tuple")
def post_form_param_tuple(items: tuple = Form(...)):
    return items


client = TestClient(app)


def test_python_list_param_as_form():
    response = client.post(
        "/form/python-list", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["first", "second", "third"]


def test_python_set_param_as_form():
    response = client.post(
        "/form/python-set", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert set(response.json()) == {"first", "second", "third"}


def test_python_tuple_param_as_form():
    response = client.post(
        "/form/python-tuple", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["first", "second", "third"]
