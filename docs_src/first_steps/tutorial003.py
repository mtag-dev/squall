from squall import Squall

app = Squall()


@app.get("/")
def root():
    return {"message": "Hello World"}
