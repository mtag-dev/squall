from dataclasses import dataclass

from squall import Body, Squall
from squall.testclient import TestClient

app = Squall()

media_type = "application/vnd.api+json"


# NOTE: These are not valid JSON:API resources
# but they are fine for testing requestBody with custom media_type
@dataclass
class Product:
    name: str
    price: float


@app.post("/products")
async def create_product(data: Product = Body(..., media_type=media_type, embed=True)):
    pass  # pragma: no cover


create_product_request_body = {
    "content": {
        "application/vnd.api+json": {"schema": {"$ref": "#/components/schemas/Product"}}
    },
    "required": None,
}

client = TestClient(app)


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    openapi_schema = response.json()
    assert (
        openapi_schema["paths"]["/products"]["post"]["requestBody"]
        == create_product_request_body
    )
