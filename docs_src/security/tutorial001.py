from squall import Depends, Squall
from squall.security import OAuth2PasswordBearer

app = Squall()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}
