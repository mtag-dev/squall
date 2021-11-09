import ast
import typing
from ast import (
    Assign,
    Attribute,
    Call,
    Compare,
    Constant,
    Expr,
    FunctionDef,
    Gt,
    GtE,
    If,
    Is,
    List,
    Load,
    Module,
    Name,
    Not,
    Pass,
    Return,
    Store,
    Subscript,
    Tuple,
    UnaryOp,
    arguments,
    fix_missing_locations,
)
from types import CodeType, FunctionType


class Validator:
    def __init__(self):
        self.rules = []

    def add_rule(
        self,
        check: str,
        source: str,
        key: str,
        optional: bool = False,
        cast: typing.Optional[typing.Any] = None,
        gt: typing.Optional[float] = None,
        ge: typing.Optional[float] = None,
        lt: typing.Optional[float] = None,
        le: typing.Optional[float] = None,
        min_length: typing.Optional[int] = None,
        max_length: typing.Optional[int] = None,
        regex: typing.Optional[str] = None,
    ):
        on_none = Pass() if optional else self._violated(source, key)
        if check == "integer":
            rule = self.integer(source, key, gt=gt, ge=ge, lt=lt, le=le)
            if rule is not None:
                self.rules.append(self._if_none(source, key, [on_none], [rule]))

    def _if_none(self, source, key, on_true, on_false):
        return If(
            test=Compare(
                left=Call(
                    func=Attribute(
                        value=Name(id=source, ctx=Load()), attr="get", ctx=Load()
                    ),
                    args=[Constant(value=key)],
                    keywords=[],
                ),
                ops=[Is()],
                comparators=[Constant(value=None)],
            ),
            body=on_true,
            orelse=on_false,
        )

    def integer(
        self,
        source: str,
        key: str,
        gt: typing.Optional[int] = None,
        ge: typing.Optional[int] = None,
        lt: typing.Optional[int] = None,
        le: typing.Optional[int] = None,
    ):
        if not any([i for i in (gt, ge, lt, le) if i is not None]):
            return

        left: typing.Union[Constant, Subscript]
        ops, comparators = [], []

        if lt is not None:
            comparators.append(Constant(value=lt))
            ops.append(Gt())
        elif le is not None:
            comparators.append(Constant(value=le))
            ops.append(GtE())

        comparators.append(
            Subscript(
                value=Name(id=source, ctx=Load()), slice=Constant(value=key), ctx=Load()
            )
        )

        if gt is not None:
            comparators.append(Constant(value=gt))
            ops.append(Gt())
        if ge is not None:
            comparators.append(Constant(value=ge))
            ops.append(GtE())

        if ops:
            compare = Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
            return If(
                test=UnaryOp(op=Not(), operand=compare),
                body=[self._violated(source, key)],
                orelse=[],
            )

    def _violated(self, source, key):
        return Expr(
            value=Call(
                func=Attribute(
                    value=Name(id="violates", ctx=Load()), attr="append", ctx=Load()
                ),
                args=[
                    Tuple(
                        elts=[Constant(value=source), Constant(value=key)], ctx=Load()
                    )
                ],
                keywords=[],
            ),
        )

    def build(self):
        rows = []
        assign = Assign()
        assign.targets = [Name(id="violates", ctx=Store())]
        assign.value = List(elts=[], ctx=Load())
        rows.append(assign)
        rows.extend(self.rules)
        rows.append(Return(value=Name(id="violates", ctx=Load())))

        function_ast = FunctionDef(
            name="validator",
            args=arguments(
                args=[
                    ast.arg("param"),
                ],
                vararg=None,
                kwarg=None,
                defaults=[],
                kwonlyargs=[],
                kw_defaults=[],
                posonlyargs=[],
            ),
            body=rows,
            type_ignores=[],
            decorator_list=[],
        )
        module_ast = Module(body=[function_ast], type_ignores=[])
        fix_missing_locations(module_ast)
        print(ast.dump(ast.parse(module_ast)))

        module_code = compile(module_ast, "<not_a_file>", "exec")
        function_code = [c for c in module_code.co_consts if isinstance(c, CodeType)][0]

        return FunctionType(function_code, {})


if __name__ == "__main__":
    validator = Validator()
    validator.add_rule("integer", "param", "orders", gt=20)
    validator.add_rule("integer", "param", "items", gt=20, optional=True)
    validation_handler = validator.build()

    import timeit

    NUMBER = 100_000

    a = {
        "orders": 30,
        "items": 40,
        "items2": 40,
        "items3": 40,
        "items4": 40,
        "items5": 40,
        "items6": 40,
        "items7": 40,
    }
    base = timeit.timeit(lambda: 1, number=NUMBER)
    asted = timeit.timeit(lambda: validation_handler(a), number=NUMBER) - base
    print("NEW (ast)", asted)

    from pydantic import BaseModel, validator

    class Params(BaseModel):
        orders: int
        items: typing.Optional[int] = None

        @validator("orders", pre=True, always=True)
        def set_orders(cls, v):
            if v <= 20:
                raise ValueError()
            return v

        @validator("items", pre=True, always=True)
        def set_items(cls, v):
            if v is not None and v <= 20:
                raise ValueError()
            return v

    pydanted = timeit.timeit(lambda: Params.validate(a), number=NUMBER) - base
    print("Old (Pydantic)", pydanted)

    # NEW(ast)
    # 0.0374231
    # Old(Pydantic)
    # 0.8141576

#
# class Param(Input):
#     pass
#
#
# class Path(Input):
#     pass
#
#
# class Query(Input):
#     pass
#
#
# class Header(Input):
#     pass
#
#
# class Cookie(Input):
#     pass
#
#
# class Body(Input):
#     pass
#
#
# class Form(Input):
#     pass
#
#
# class File(Input):
#     pass
#
#
# def get_default_args(func):
#     signature = inspect.signature(func)
#     return {
#         k: v.default
#         for k, v in signature.parameters.items()
#         if v.default is not inspect.Parameter.empty
#     }
