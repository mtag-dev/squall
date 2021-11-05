from squall import File, Squall, UploadFile

app = Squall()


@app.router.post("/files/")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}


@app.router.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}
