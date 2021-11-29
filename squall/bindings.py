from dataclasses import dataclass
from typing import Any, Optional

from squall.params import Body


@dataclass
class RequestField:
    name: str
    model: Any
    settings: Optional[Body] = None


@dataclass
class ResponseField:
    model: Any
