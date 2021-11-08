from squall import Depends
from squall.router import Router

from ..dependencies import get_token_header

router = Router(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)


@router.post("/")
async def update_admin():
    return {"message": "Admin getting schwifty"}
