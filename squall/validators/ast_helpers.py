import ast
import typing


def setitem(
    entity_name: str,
    key: str,
    value: typing.Any,
) -> ast.Assign:
    """Set dictionary item value.

    Generates following code: `entity_name[key] = value`
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
    """
    return ast.Subscript(
        value=ast.Name(id=entity_name, ctx=ast.Load()), slice=key, ctx=ast.Load()
    )


def getattribute(entity_name: str, attribute: str) -> ast.Attribute:
    """Get object attribute.

    Generates following code: `entity_name.attribute`
    """
    return ast.Attribute(
        value=ast.Name(id=entity_name, ctx=ast.Load()),
        attr=attribute,
        ctx=ast.Load(),
    )


def call(
    entity_name: str,
    attribute: typing.Optional[str] = None,
    args: typing.Optional[typing.List[typing.Any]] = None,
    is_expression: bool = False,
) -> typing.Union[ast.Call, ast.Expr]:
    """Generates function or attribute calling.
    Use is is_expression=True if the call is not a part of another expression

    Without attributes and args: `entity_name()`
    Without attribute: `entity_name(args)`
    With attribute and args: `entity_name.attribute(args)`
    """
    args = args or []
    func: typing.Union[ast.Name, ast.Attribute]
    if attribute is None:
        func = ast.Name(id=entity_name, ctx=ast.Load())
    else:
        func = getattribute(entity_name, attribute)

    if is_expression:
        return ast.Expr(value=ast.Call(func=func, args=args, keywords=[]))
    return ast.Call(func=func, args=args, keywords=[])


def append(list_name: str, value: typing.Any) -> ast.Expr:
    """Appends item to given list

    Generates following code: `list_name.append(value)`
    """
    expr = call(
        entity_name=list_name, attribute="append", args=[value], is_expression=True
    )
    assert isinstance(expr, ast.Expr)  # MyPy hack
    return expr
