# from squall import APIRouter, Request, Squall
# from squall.responses import JSONResponse
# from squall.testclient import TestClient
#
# app = Squall()
# router = APIRouter()
#
#
# @router.route("/items/")
# def read_items(request: Request):
#     return JSONResponse({"hello": "world"})
#
#
# app.include_router(router)
#
# client = TestClient(app)
#
#
# def test_sub_router():
#     response = client.get("/items/")
#     assert response.status_code == 200, response.text
#     assert response.json() == {"hello": "world"}
