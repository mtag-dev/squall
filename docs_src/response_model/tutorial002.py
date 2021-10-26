from typing import Optional

from pydantic import BaseModel, EmailStr

from squall import Squall

app = Squall()


class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None


# Don't do this in production!
@app.post("/user/", response_model=UserIn)
async def create_user(user: UserIn):
    return user
