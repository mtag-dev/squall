from squall import Squall
from squall.middleware.cors import CORSMiddleware

app = Squall()

origins = [
    "http://localhost.mtag.dev",
    "https://localhost.mtag.dev",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.router.get("/")
async def main():
    return {"message": "Hello World"}
