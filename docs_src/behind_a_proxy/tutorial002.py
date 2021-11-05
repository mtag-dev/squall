from squall import Request, Squall

app = Squall(root_path="/api/v1")


@app.router.get("/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": request.scope.get("root_path")}
