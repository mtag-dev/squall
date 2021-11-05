from squall import Squall

app = Squall()


@app.router.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
