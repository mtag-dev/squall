import re
from typing import Any, Dict, Set, Union

from squall.datastructures import DefaultPlaceholder, DefaultType


def get_path_param_names(path: str) -> Set[str]:
    return set(re.findall("{(.*?)}", path))


def generate_operation_id_for_path(*, name: str, path: str, method: str) -> str:
    operation_id = name + path
    operation_id = re.sub("[^0-9a-zA-Z_]", "_", operation_id)
    operation_id = operation_id + "_" + method.lower()
    return operation_id


def deep_dict_update(main_dict: Dict[Any, Any], update_dict: Dict[Any, Any]) -> None:
    for key in update_dict:
        if (
            key in main_dict
            and isinstance(main_dict[key], dict)
            and isinstance(update_dict[key], dict)
        ):
            deep_dict_update(main_dict[key], update_dict[key])
        else:
            main_dict[key] = update_dict[key]


def get_value_or_default(
    first_item: Union[DefaultPlaceholder, DefaultType],
    *extra_items: Union[DefaultPlaceholder, DefaultType],
) -> Union[DefaultPlaceholder, DefaultType]:
    """
    Pass items or `DefaultPlaceholder`s by descending priority.

    The first one to _not_ be a `DefaultPlaceholder` will be returned.

    Otherwise, the first item (a `DefaultPlaceholder`) will be returned.
    """
    items = (first_item,) + extra_items
    for item in items:
        if not isinstance(item, DefaultPlaceholder):
            return item
    return first_item
