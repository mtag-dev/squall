from squall import Depends, Squall
from squall.security import HTTPBasic, HTTPBasicCredentials

app = Squall()

security = HTTPBasic()


@app.get("/users/me")
def read_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    return {"username": credentials.username, "password": credentials.password}
