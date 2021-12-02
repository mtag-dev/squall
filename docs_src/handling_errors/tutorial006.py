from squall import HTTPException, Squall
from squall.exception_handlers import (
    http_exception_handler,
    request_payload_validation_exception_handler,
)
from squall.exceptions import RequestPayloadValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = Squall()


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!: {repr(exc)}")
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestPayloadValidationError)
async def validation_exception_handler(request, exc):
    print(f"OMG! The client sent invalid data!: {exc}")
    return await request_payload_validation_exception_handler(request, exc)


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}
