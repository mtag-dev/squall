from squall import Squall

app = Squall()


@app.router.get("/")
def root():
    return {"message": "Hello World"}
