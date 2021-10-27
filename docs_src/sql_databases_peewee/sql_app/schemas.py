from typing import Any, List, Optional

import peewee
from pydantic import Field, dataclasses
from pydantic.utils import GetterDict


class PeeweeGetterDict(GetterDict):
    def get(self, key: Any, default: Any = None):
        res = getattr(self._obj, key, default)
        if isinstance(res, peewee.ModelSelect):
            return list(res)
        return res


@dataclasses.dataclass
class ItemBase:
    title: str = Field(...)
    description: Optional[str] = None


@dataclasses.dataclass
class ItemCreate(ItemBase):
    pass


class Config:
    orm_mode = True
    getter_dict = PeeweeGetterDict


@dataclasses.dataclass(config=Config)
class Item(ItemBase):
    id: int = Field(...)
    owner: int = Field(...)


@dataclasses.dataclass
class UserBase:
    email: str = Field(...)


@dataclasses.dataclass
class UserCreate(UserBase):
    password: str = Field(...)


class Config:
    orm_mode = True
    getter_dict = PeeweeGetterDict


@dataclasses.dataclass(config=Config)
class User(UserBase):
    id: int = Field(...)
    is_active: bool = Field(...)
    items: List[Item] = Field(default_factory=list)
