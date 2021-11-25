import ast
import typing


def setitem(
    entity_name: str,
    key: str,
    value: typing.Any,
) -> ast.Assign:
    """Set dictionary item value.
    Generates following code: `entity_name[key] = value`

    :param entity_name: dictionary variable name
    :param key: dictionary key or list index
    :param value: value expression
    :returns: an assign expression
    """
    subscript = ast.Subscript(
        value=ast.Name(id=entity_name, ctx=ast.Load()),
        slice=ast.Constant(value=key),
        ctx=ast.Store(),
    )

    return ast.Assign(targets=[subscript], value=value)


def getitem(
    entity_name: str, key: typing.Union[ast.Constant, ast.Subscript]
) -> ast.Subscript:
    """Get dictionary item value.
    Generates following code: `entity_name[key]`

    :param entity_name: dictionary variable name
    :param key: dictionary key or list index
    :returns: a subscript expression
    """
    return ast.Subscript(
        value=ast.Name(id=entity_name, ctx=ast.Load()), slice=key, ctx=ast.Load()
    )


def getattribute(
    entity_name: str, attributes: typing.List[str]
) -> typing.Union[ast.Name, ast.Attribute]:
    """Get object attribute.

    Generates following code:
        getattribute(entity_name, [attribute]) -> `entity_name.attribute`
        getattribute(entity_name, [attribute, get]) -> `entity_name.attribute.get`

    :param entity_name: dictionary variable name
    :param attributes: list of attributes names
    """
    value: typing.Union[ast.Name, ast.Attribute] = ast.Name(
        id=entity_name, ctx=ast.Load()
    )
    for attribute in attributes:
        value = ast.Attribute(
            value=value,
            attr=attribute,
            ctx=ast.Load(),
        )
    return value


def call(
    entity_name: str,
    attributes: typing.Optional[typing.List[str]] = None,
    args: typing.Optional[typing.List[typing.Any]] = None,
    is_standalone: bool = False,
) -> typing.Union[ast.Call, ast.Expr]:
    """Generates function or attribute calling.
    Use is is_expression=True if the call is not a part of another expression

    Without attributes and args: `entity_name()`
    Without attribute: `entity_name(args)`
    With attribute and args: `entity_name.attribute(args)`

    :param entity_name: dictionary variable name
    :param attributes: list of attributes names
    :param args: list of arguments expressions
    :param is_standalone: is a part of another expression or not. True if not
    """
    args = args or []
    func: typing.Union[ast.Name, ast.Attribute]
    if attributes:
        func = getattribute(entity_name, attributes)
    else:
        func = ast.Name(id=entity_name, ctx=ast.Load())

    if is_standalone:
        return ast.Expr(value=ast.Call(func=func, args=args, keywords=[]))
    return ast.Call(func=func, args=args, keywords=[])


def append(list_name: str, value: typing.Any) -> ast.Expr:
    """Appends item to given list

    Generates following code: `list_name.append(value)`
    :param list_name: list variable name
    :param value: expression for getting of value that should be appended
    :returns: append expression ast
    """
    expr = call(
        entity_name=list_name, attributes=["append"], args=[value], is_standalone=True
    )
    assert isinstance(expr, ast.Expr)  # MyPy hack
    return expr


def assign(name: str, value: typing.Any) -> ast.Assign:
    """Assign value to the given variable name

    Generates the following code: `name = value`

    :param name: name of variable which should get the value
    :param value: get target value expression
    :returns: assign ast
    """
    return ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())], value=value)
