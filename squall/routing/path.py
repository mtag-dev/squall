import inspect
import re
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from squall import convertors, params

PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


class Path:
    def __init__(self, path: str, handler: Callable[..., Any]) -> None:
        self.path = path
        self.handler = handler

    def append_left(self, prefix: str) -> None:
        if not prefix.endswith("/"):
            prefix += "/"
        self.path = urljoin(prefix, self.path.strip("/"))
        print(self.path)

    @property
    def path_params(self) -> List[Tuple[str, Optional[str]]]:
        result, names = [], []
        for param in PARAM_REGEX.finditer(self.path):
            name, suffix = param.groups("")
            names.append(name)
            convertor = suffix.lstrip(":") if suffix else None
            result.append((name, convertor))

        if duplicates := [i for i, cnt in Counter(names).items() if cnt > 1]:
            raise ValueError(
                f'Path "{self.path}" contains '
                f"duplicate params: {', '.join(duplicates)}"
            )

        return result

    @property
    def schema_path(self) -> str:
        result = self.path
        for match in PARAM_REGEX.finditer(self.path):
            param_name, convertor_type = match.groups("")
            result = result.replace(
                "{" f"{param_name}{convertor_type}" "}",
                "{" f"{param_name}" "}",
            )
        return result

    @property
    def router_path(self) -> str:
        result = self.schema_path
        from_handler = self.get_path_params_from_handler()
        for param_name, convertor_name in self.path_params:
            if convertor_name := convertor_name or from_handler.get(param_name):
                result = result.replace(
                    "{" f"{param_name}" "}",
                    "{" f"{param_name}:{convertor_name}" "}",
                )
        return result

    def get_path_params_from_handler(self) -> Dict[str, Optional[str]]:
        results = {}
        path_params = dict(self.path_params)
        for k, v in inspect.signature(self.handler).parameters.items():
            name = k
            if isinstance(v.default, params.Path):
                if alias := v.default.alias:
                    name = alias
            elif v.default is v.empty:
                name = k
            else:
                continue

            if name not in path_params:
                continue

            validate = path_params[name]

            if v.annotation != v.empty:
                if convertor := convertors.database.get_by_type(v.annotation):
                    if validate is None:
                        validate = convertor.alias
                    elif convertor.alias != path_params[name]:
                        raise ValueError(
                            "Parameter {name} have different annotation and convertor types: "
                            f"{convertor.alias} != {path_params[name]}"
                        )

            results[name] = validate
        return results


# if __name__ == "__main__":
#     from uuid import UUID
#
#     def handler(aaa, bbb: UUID):
#         pass
#
#     p = Path("/aaa/{aaa:uuid}/bbb/{bbb}/ccc/{ccc:int}", handler)
#     p.append_left("/api/v1")
#     print(p.router_path)
#     print(p.schema_path)
