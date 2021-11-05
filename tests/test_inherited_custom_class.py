import uuid

import pytest
from pydantic import dataclasses
from squall import Squall
from squall.testclient import TestClient

app = Squall()


class MyUuid:
    def __init__(self, uuid_string: str):
        self.uuid = uuid_string

    def __str__(self):
        return self.uuid

    @property  # type: ignore
    def __class__(self):
        return uuid.UUID

    @property
    def __dict__(self):
        """Spoof a missing __dict__ by raising TypeError, this is how
        asyncpg.pgroto.pgproto.UUID behaves"""
        raise TypeError("vars() argument must have __dict__ attribute")


@app.router.get("/fast_uuid")
def return_fast_uuid():
    # I don't want to import asyncpg for this test so I made my own UUID
    # Import asyncpg and uncomment the two lines below for the actual bug

    # from asyncpg.pgproto import pgproto
    # asyncpg_uuid = pgproto.UUID("a10ff360-3b1e-4984-a26f-d3ab460bdb51")

    asyncpg_uuid = MyUuid("a10ff360-3b1e-4984-a26f-d3ab460bdb51")
    assert isinstance(asyncpg_uuid, uuid.UUID)
    assert type(asyncpg_uuid) != uuid.UUID
    with pytest.raises(TypeError):
        vars(asyncpg_uuid)
    return {"fast_uuid": asyncpg_uuid}


class Config:
    arbitrary_types_allowed = True


@dataclasses.dataclass(config=Config)
class SomeCustomClass:
    a_uuid: MyUuid


@app.router.get("/get_custom_class")
def return_some_user():
    # Test that the fix also works for custom pydantic classes
    return SomeCustomClass(a_uuid=MyUuid("b8799909-f914-42de-91bc-95c819218d01"))


client = TestClient(app)


@pytest.mark.skip(reason="Mechanism for serialisation needed")
def test_dt():
    with client:
        response_simple = client.get("/fast_uuid")
        response_pydantic = client.get("/get_custom_class")

    assert response_simple.json() == {
        "fast_uuid": "a10ff360-3b1e-4984-a26f-d3ab460bdb51"
    }

    assert response_pydantic.json() == {
        "a_uuid": "b8799909-f914-42de-91bc-95c819218d01"
    }
