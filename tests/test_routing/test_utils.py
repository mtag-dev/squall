from typing import Optional

from squall.params import Cookie, Header, Num, Path, Query, Str
from squall.routing.utils import get_handler_head_params


def test_get_handler_args_no_args():
    def handler():
        pass

    assert get_handler_head_params(handler, {}) == []


def test_get_handler_args_no_annotation():
    def handler(a, b=Query(...), c=Path(...), d=Header(...), e=Cookie(...)):
        pass

    params = get_handler_head_params(handler, {})
    assert params[0].convertor == "str"
    assert params[0].default == Ellipsis
    assert params[0].statements == {}
    assert params[0].name == "b"
    assert params[0].alias == "b"
    assert params[0].source == "query_params"
    assert params[0].validate is None

    assert params[1].convertor == "str"
    assert params[1].default == Ellipsis
    assert params[1].statements == {}
    assert params[1].name == "c"
    assert params[1].alias == "c"
    assert params[1].source == "path_params"
    assert params[1].validate is None

    assert params[2].convertor == "str"
    assert params[2].default == Ellipsis
    assert params[2].statements == {}
    assert params[2].name == "d"
    assert params[2].alias == "d"
    assert params[2].source == "headers"
    assert params[2].validate is None

    assert params[3].convertor == "str"
    assert params[3].default == Ellipsis
    assert params[3].statements == {}
    assert params[3].name == "e"
    assert params[3].alias == "e"
    assert params[3].source == "cookies"
    assert params[3].validate is None


def test_get_handler_args_alias():
    def handler(
        b=Query(..., alias="from_b"),
        c=Path(..., alias="from_c"),
        d=Header(..., alias="from_d"),
        e=Cookie(..., alias="from_e"),
    ):
        pass

    params = get_handler_head_params(handler, {})
    assert params[0].convertor == "str"
    assert params[0].default == Ellipsis
    assert params[0].statements == {}
    assert params[0].name == "b"
    assert params[0].alias == "from_b"
    assert params[0].source == "query_params"
    assert params[0].validate is None

    assert params[1].convertor == "str"
    assert params[1].default == Ellipsis
    assert params[1].statements == {}
    assert params[1].name == "c"
    assert params[1].alias == "from_c"
    assert params[1].source == "path_params"
    assert params[1].validate is None

    assert params[2].convertor == "str"
    assert params[2].default == Ellipsis
    assert params[2].statements == {}
    assert params[2].name == "d"
    assert params[2].alias == "from_d"
    assert params[2].source == "headers"
    assert params[2].validate is None

    assert params[3].convertor == "str"
    assert params[3].default == Ellipsis
    assert params[3].statements == {}
    assert params[3].name == "e"
    assert params[3].alias == "from_e"
    assert params[3].source == "cookies"
    assert params[3].validate is None


def test_get_handler_args_annotations():
    def handler(b: int = Path(), c: str = Path(), d: bytes = Path(), e: float = Path()):
        pass

    params = get_handler_head_params(handler, {})
    assert params[0].convertor == "int"
    assert params[0].default == Ellipsis
    assert params[0].statements == {}
    assert params[0].name == "b"
    assert params[0].source == "path_params"
    assert params[0].validate is None

    assert params[1].convertor == "str"
    assert params[1].default == Ellipsis
    assert params[1].statements == {}
    assert params[1].name == "c"
    assert params[1].source == "path_params"
    assert params[1].validate is None

    assert params[2].convertor == "bytes"
    assert params[2].default == Ellipsis
    assert params[2].statements == {}
    assert params[2].name == "d"
    assert params[2].source == "path_params"
    assert params[2].validate is None

    assert params[3].convertor == "float"
    assert params[3].default == Ellipsis
    assert params[3].statements == {}
    assert params[3].name == "e"
    assert params[3].source == "path_params"
    assert params[3].validate is None


def test_get_handler_args_direct_defaults():
    def handler(
        a: str,
        b: int = Query(1),
        c: str = Query("Hey"),
        d: bytes = Query(b"Hey"),
        e: float = Query(3.14),
    ):
        pass

    params = get_handler_head_params(handler, {"a": None})
    assert params[0].convertor == "str"
    assert params[0].default == Ellipsis
    assert params[0].statements == {}
    assert params[0].name == "a"
    assert params[0].source == "path_params"
    assert params[0].validate is None

    assert params[1].convertor == "int"
    assert params[1].default == 1
    assert params[1].statements == {}
    assert params[1].name == "b"
    assert params[1].source == "query_params"
    assert params[1].validate is None

    assert params[2].convertor == "str"
    assert params[2].default == "Hey"
    assert params[2].statements == {}
    assert params[2].name == "c"
    assert params[2].source == "query_params"
    assert params[2].validate is None

    assert params[3].convertor == "bytes"
    assert params[3].default == b"Hey"
    assert params[3].statements == {}
    assert params[3].name == "d"
    assert params[3].source == "query_params"
    assert params[3].validate is None

    assert params[4].convertor == "float"
    assert params[4].default == 3.14
    assert params[4].statements == {}
    assert params[4].name == "e"
    assert params[4].source == "query_params"
    assert params[4].validate is None


def test_get_handler_args_assigned_instance_defaults():
    def handler(
        a: str = Path(),
        b: int = Path(1),
        c: str = Query("Hey"),
        d: bytes = Header(b"Hey"),
        e: float = Cookie(3.14),
    ):
        pass

    params = get_handler_head_params(handler, {})
    assert params[0].convertor == "str"
    assert params[0].default == Ellipsis
    assert params[0].statements == {}
    assert params[0].name == "a"
    assert params[0].source == "path_params"
    assert params[0].validate is None

    assert params[1].convertor == "int"
    assert params[1].default == 1
    assert params[1].statements == {}
    assert params[1].name == "b"
    assert params[1].source == "path_params"
    assert params[1].validate is None

    assert params[2].convertor == "str"
    assert params[2].default == "Hey"
    assert params[2].statements == {}
    assert params[2].name == "c"
    assert params[2].source == "query_params"
    assert params[2].validate is None

    assert params[3].convertor == "bytes"
    assert params[3].default == b"Hey"
    assert params[3].statements == {}
    assert params[3].name == "d"
    assert params[3].source == "headers"
    assert params[3].validate is None

    assert params[4].convertor == "float"
    assert params[4].default == 3.14
    assert params[4].statements == {}
    assert params[4].name == "e"
    assert params[4].source == "cookies"
    assert params[4].validate is None


def test_get_handler_args_validation_parameters():
    def handler(
        a: Optional[str] = Path(None, valid=Str(min_len=2)),
        b: int = Path(1, valid=Num(ge=1, le=2)),
        c: str = Query("Hey", valid=Str(min_len=2, max_len=5)),
        d: bytes = Header(b"Hey", valid=Str(min_len=2, max_len=5)),
        e: float = Cookie(3.14, valid=Num(ge=3.14, le=3.15)),
    ):
        pass

    params = get_handler_head_params(handler, {})
    assert params[0].convertor == "str"
    assert params[0].default is None
    assert params[0].statements["min_len"] == 2
    assert params[0].name == "a"
    assert params[0].source == "path_params"
    assert params[0].validate == "string"

    assert params[1].convertor == "int"
    assert params[1].default == 1
    assert params[1].statements == {"ge": 1, "gt": None, "le": 2, "lt": None}
    assert params[1].name == "b"
    assert params[1].source == "path_params"
    assert params[1].validate == "numeric"

    assert params[2].convertor == "str"
    assert params[2].default == "Hey"
    assert params[2].statements == {"max_len": 5, "min_len": 2}
    assert params[2].name == "c"
    assert params[2].source == "query_params"
    assert params[2].validate == "string"

    assert params[3].convertor == "bytes"
    assert params[3].default == b"Hey"
    assert params[3].statements == {"max_len": 5, "min_len": 2}
    assert params[3].name == "d"
    assert params[3].source == "headers"
    assert params[3].validate == "string"

    assert params[4].convertor == "float"
    assert params[4].default == 3.14
    assert params[4].statements == {"ge": 3.14, "gt": None, "le": 3.15, "lt": None}
    assert params[4].name == "e"
    assert params[4].source == "cookies"
    assert params[4].validate == "numeric"
