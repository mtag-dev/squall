"""Squall framework"""

__version__ = "0.0.1a"

from starlette import status as status

from .applications import Squall as Squall
from .background import BackgroundTasks as BackgroundTasks
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException

# from .param_functions import Depends as Depends
from .params import Body as Body
from .params import Cookie as Cookie
from .params import File as File
from .params import Form as Form
from .params import Header as Header
from .params import Path as Path
from .params import Query as Query

# from .param_functions import Security as Security
from .requests import Request as Request
from .responses import Response as Response
from .router import Router as Router
from .websockets import WebSocket as WebSocket
from .websockets import WebSocketDisconnect as WebSocketDisconnect
