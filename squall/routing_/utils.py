import inspect
from typing import Any, Callable, Dict, List, Union, get_args, get_origin

from squall.params import Cookie, Header, Param, Query

HANDLER_PARAMS_SOURCE_MAPPING = {
    Query: "query",
    Header: "header",
    Cookie: "cookie",
    Param: "param",
}


def get_handler_args(func: Callable[..., Any]) -> List[Dict[str, Any]]:
    signature = inspect.signature(func)
    results = []
    for k, v in signature.parameters.items():
        param: Dict[str, Any] = {"name": k}
        args, origin = get_args(v.annotation), get_origin(v.annotation)
        if origin is Union:
            if type(None) in args:
                param["optional"] = True
                param["convert"] = args[0].__name__
        elif hasattr(v.annotation, "__name__") and v.annotation.__name__ != "_empty":
            param["convert"] = v.annotation.__name__

        if hasattr(v.default, "default"):
            if v.default.default != Ellipsis:
                param["default"] = v.default.default
            param["source"] = HANDLER_PARAMS_SOURCE_MAPPING.get(type(v.default))

            for known_param in (
                "gt",
                "ge",
                "lt",
                "le",
                "min_length",
                "max_length",
                "origin",
            ):
                value = getattr(v.default, known_param, None)
                if value is not None:
                    param[known_param] = value

        elif v.default != v.empty:
            param["default"] = v.default
            param["source"] = "param"
        else:
            param["source"] = "param"

        if param["source"] is not None:
            results.append(param)

    return results
