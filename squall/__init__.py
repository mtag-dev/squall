"""Squall framework"""

__version__ = "0.2.1"

from squall.routing.router import Router as Router

from .applications import Squall as Squall
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException
from .params import Body as Body
from .params import Cookie as Cookie
from .params import File as File
from .params import Form as Form
from .params import Header as Header
from .params import Num as Num
from .params import Path as Path
from .params import Query as Query
from .params import Str as Str
from .requests import Request as Request
from .responses import Response as Response
from .websockets import WebSocket as WebSocket
