from pydantic import BaseSettings
from squall import Squall


class Settings(BaseSettings):
    openapi_url: str = "/openapi.json"


settings = Settings()

app = Squall(openapi_url=settings.openapi_url)


@app.router.get("/")
def root():
    return {"message": "Hello World"}
