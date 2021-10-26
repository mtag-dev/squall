from squall import Squall

from . import a, b

app = Squall()

app.include_router(a.router, prefix="/a")
app.include_router(b.router, prefix="/b")
