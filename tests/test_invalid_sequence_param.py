from typing import Dict, List, Optional, Tuple

import pytest
from pydantic import BaseModel
from squall import Query, Squall


def test_invalid_sequence():
    with pytest.raises(AssertionError):
        app = Squall()

        class Item(BaseModel):
            title: str

        @app.router.get("/items/")
        def read_items(q: List[Item] = Query(None)):
            pass  # pragma: no cover


def test_invalid_tuple():
    with pytest.raises(AssertionError):
        app = Squall()

        class Item(BaseModel):
            title: str

        @app.router.get("/items/")
        def read_items(q: Tuple[Item, Item] = Query(None)):
            pass  # pragma: no cover


def test_invalid_dict():
    with pytest.raises(AssertionError):
        app = Squall()

        class Item(BaseModel):
            title: str

        @app.router.get("/items/")
        def read_items(q: Dict[str, Item] = Query(None)):
            pass  # pragma: no cover


def test_invalid_simple_dict():
    with pytest.raises(AssertionError):
        app = Squall()

        class Item(BaseModel):
            title: str

        @app.router.get("/items/")
        def read_items(q: Optional[dict] = Query(None)):
            pass  # pragma: no cover
