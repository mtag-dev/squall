from squall import Body
from squall.router import Router

router = Router(prefix="/b")


@router.post("/compute/")
def compute(a: int = Body(...), b: str = Body(...)):
    return {"a": a, "b": b}
