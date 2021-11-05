from squall import Squall

app = Squall()


@app.router.get("/app")
def read_main():
    return {"message": "Hello World from main app"}


subapi = Squall()


@subapi.router.get("/sub")
def read_sub():
    return {"message": "Hello World from sub API"}


app.mount("/subapi", subapi)
