from squall import Squall
from squall.routing.router import Router
from squall.testclient import TestClient

app = Squall()

router = Router(prefix="/{segment}")


@router.get("/users/{id}")
def read_user(segment: str, id: str):
    return {"segment": segment, "id": id}


app.include_router(router)


client = TestClient(app)


def test_get():
    response = client.get("/seg/users/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"segment": "seg", "id": "foo"}
