from squall import Squall
from squall.staticfiles import StaticFiles

app = Squall()

app.mount("/static", StaticFiles(directory="static"), name="static")
