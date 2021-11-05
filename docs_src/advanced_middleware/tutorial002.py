from squall import Squall
from squall.middleware.trustedhost import TrustedHostMiddleware

app = Squall()

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"]
)


@app.router.get("/")
async def main():
    return {"message": "Hello World"}
