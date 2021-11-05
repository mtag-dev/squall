from squall import Squall
from squall.responses import FileResponse

some_file_path = "large-video-file.mp4"
app = Squall()


@app.router.get("/")
async def main():
    return FileResponse(some_file_path)
