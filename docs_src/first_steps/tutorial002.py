from squall import Squall

my_awesome_api = Squall()


@my_awesome_api.get("/")
async def root():
    return {"message": "Hello World"}
