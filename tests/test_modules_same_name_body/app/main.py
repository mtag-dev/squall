from squall import Squall

from . import a, b

app = Squall()

app.include_router(a.router)
app.include_router(b.router)
