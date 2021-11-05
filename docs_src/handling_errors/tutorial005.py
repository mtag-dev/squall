from pydantic import Field, dataclasses
from squall import Request, Squall, status
from squall.exceptions import RequestValidationError
from squall.responses import JSONResponse

app = Squall()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@dataclasses.dataclass
class Item:
    title: str = Field(...)
    size: int = Field(...)


@app.router.post("/items/")
async def create_item(item: Item):
    return item
