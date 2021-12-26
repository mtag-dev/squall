import pytest
from squall.routing.path import Path


def test_append_left():
    p = Path("/my/route", lambda: None)
    assert p.path == "/my/route"
    # append without trailing slash
    p.append_left("/api/v1")
    assert p.path == "/api/v1/my/route"
    # append with trailing slash
    p.append_left("/my_service/")
    assert p.path == "/my_service/api/v1/my/route"


def test_path_params():
    p = Path("/user/{user_id:int}/notes/{note:uuid}/type/{type}", lambda: None)
    assert p.path_params == [("user_id", "int"), ("note", "uuid"), ("type", None)]


def test_path_params_duplication():
    p = Path("/user/{user_id}/notes/{user_id:uuid}", lambda: None)
    with pytest.raises(ValueError):
        p.path_params


def test_schema_path():
    p = Path("/user/{user_id:int}/notes/{note:uuid}/type/{type}", lambda: None)
    assert p.schema_path == "/user/{user_id}/notes/{note}/type/{type}"


def test_router_path():
    async def my_handler(user_id: int, note):
        pass

    p = Path("/user/{user_id}/notes/{note:uuid}", my_handler)
    assert p.router_path == "/user/{user_id:int}/notes/{note:uuid}"


def test_get_path_params_from_handler():
    from uuid import UUID

    async def my_handler(user_id: int, note: UUID, non_path_param):
        pass

    p = Path("/user/{user_id}/notes/{note}", my_handler)
    assert p.get_path_params_from_handler() == {"user_id": "int", "note": "uuid"}


def test_get_path_params_from_handler_unknown_convertor():
    async def my_handler(user_id: int, note: bool):
        pass

    p = Path("/user/{user_id}/notes/{note}", my_handler)
    with pytest.raises(ValueError):
        p.get_path_params_from_handler()


def test_get_path_params_from_handler_different_annotation():
    async def my_handler(user_id: int):
        pass

    p = Path("/user/{user_id:str}", my_handler)
    with pytest.raises(ValueError):
        p.get_path_params_from_handler()
