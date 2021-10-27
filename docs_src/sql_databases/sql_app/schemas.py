from typing import List, Optional

from pydantic import Field, dataclasses


@dataclasses.dataclass
class ItemBase:
    title: str = Field(...)
    description: Optional[str] = None


@dataclasses.dataclass
class ItemCreate(ItemBase):
    pass


class Config:
    orm_mode = True


@dataclasses.dataclass(config=Config)
class Item(ItemBase):
    id: int = Field(...)
    owner_id: int = Field(...)


@dataclasses.dataclass
class UserBase:
    email: str = Field(...)


@dataclasses.dataclass
class UserCreate(UserBase):
    password: str = Field(...)


class Config:
    orm_mode = True


@dataclasses.dataclass(config=Config)
class User(UserBase):
    id: int = Field(...)
    is_active: bool = Field(...)
    items: List[Item] = Field(default_factory=list)
