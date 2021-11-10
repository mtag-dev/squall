import ast
import typing
from ast import (
    Assign,
    Attribute,
    Call,
    Compare,
    Constant,
    Dict,
    Expr,
    ExceptHandler,
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
    Try,
    Tuple,
    UnaryOp,
    arguments,
    fix_missing_locations,
)
from types import CodeType, FunctionType


class Validator:
    def __init__(self, args: typing.List[str]):
        self.args = args + ['convert']
        assert len(self.args) > 1, "No input parameters names configured."
        self.rules = []

    def add_rule(
        self,
        check: str,
        source: str,
        key: str,
        name: typing.Optional[str] = None,
        optional: bool = False,
        convert: typing.Optional[typing.Any] = None,
        # Both
        # eq: typing.Optional[typing.Any] = None,
        # Numeric arguments
        gt: typing.Optional[float] = None,
        ge: typing.Optional[float] = None,
        lt: typing.Optional[float] = None,
        le: typing.Optional[float] = None,
        # String arguments
        min_length: typing.Optional[int] = None,
        max_length: typing.Optional[int] = None,
        default: typing.Optional[typing.Any] = None
    ):
        assert source in self.args
        name = Constant(value=name) if name else Constant(value=key)
        on_none = []
        if default is not None:
            on_none.append(self._set_default(name, default))
        else:
            on_none.append(
                Pass() if optional else self._violated(source, key, "Can't be None")
            )

        if check == "integer":
            rule = self.integer(source, key, name, gt=gt, ge=ge, lt=lt, le=le)
            if convert is not None:
                rule = self._try_convert(source, key, convert, than=rule)
        elif check == "string":
            rule = self.string(source, key, name, min_length=min_length, max_length=max_length)
            if convert is not None:
                rule = self._try_convert(source, key, convert, than=rule)
        if rule is not None:
            self.rules.append(self._if_none(source, key, on_none, rule))

    def _set_default(self, name, default):
        return Assign(
            targets=[
                Subscript(
                    value=Name(id='results', ctx=Load()),
                    slice=name,
                    ctx=Store())],
            value=Constant(value=default)
        )

    def _try_convert(self, source, key, func, than):
        _try = Try()
        _try.orelse = []
        _try.finalbody = []
        _try.handlers = [
            ExceptHandler(
                body=[self._violated(source, key, f'Cast of `{func}` failed')]
            )
        ]
        _try.body = [
            Assign(
                targets=[
                    Subscript(
                        value=Name(id=source, ctx=Load()),
                        slice=Constant(value=key),
                        ctx=Store())],
                value=Call(
                    func=Subscript(
                        value=Name(id='convert', ctx=Load()),
                        slice=Constant(value=func),
                        ctx=Load()
                    ),
                    args=[
                        Subscript(
                            value=Name(id=source, ctx=Load()),
                            slice=Constant(value=key),
                            ctx=Load())],
                    keywords=[]))
            ,
            *than
        ]
        return [_try]

    def _if_none(self, source, key, on_true, on_false):
        return If(
            test=Compare(
                left=Call(
                    func=Attribute(
                        value=Name(id=source, ctx=Load()),
                        attr="get",
                        ctx=Load()
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

    def _copy(self, source, key, name):
        """"""
        target = Subscript(
            value=Name(id='results', ctx=Load()), slice=name, ctx=Store()
        )
        source = Subscript(
            value=Name(id=source, ctx=Load()), slice=Constant(value=key), ctx=Load()
        )

        return Assign(targets=[target], value=source)

    def integer(
        self,
        source: str,
        key: str,
        name: Constant,
        gt: typing.Optional[int] = None,
        ge: typing.Optional[int] = None,
        lt: typing.Optional[int] = None,
        le: typing.Optional[int] = None,
    ):
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
            produce = self._copy(source, key, name)
            return [If(
                test=UnaryOp(op=Not(), operand=compare),
                body=[self._violated(source, key, 'Validation error')],
                orelse=[produce],
            )]

    def string(
        self,
        source: str,
        key: str,
        name: Constant,
        min_length: typing.Optional[int] = None,
        max_length: typing.Optional[int] = None,
    ):
        get_length = Assign(
            targets=[
                Name(id=f'{name}_len', ctx=Store())],
            value=Call(
                func=Name(id='len', ctx=Load()),
                args=[
                    Subscript(
                        value=Name(id=source, ctx=Load()), slice=Constant(value=key), ctx=Load()
                    )
                ],
                keywords=[])
        )

        ops, comparators = [], []
        if max_length is not None:
            comparators.append(Constant(value=max_length))
            ops.append(GtE())

        comparators.append(Name(id=f'{name}_len', ctx=Load()))

        if min_length is not None:
            comparators.append(Constant(value=min_length))
            ops.append(GtE())

        if ops:
            compare = Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
            produce = self._copy(source, key, name)
            return [
                get_length,
                If(
                    test=UnaryOp(op=Not(), operand=compare),
                    body=[self._violated(source, key, 'Validation error')],
                    orelse=[produce],
                )
            ]

    def _violated(self, source, key, reason):
        return Expr(
            value=Call(
                func=Attribute(
                    value=Name(id="violates", ctx=Load()), attr="append", ctx=Load()
                ),
                args=[
                    Tuple(
                        elts=[Constant(value=source), Constant(value=key), Constant(value=reason)], ctx=Load()
                    )
                ],
                keywords=[],
            ),
        )

    def build(self):
        rows = []
        defs = [
            {
                "name": "results",
                "exp": Dict(keys=[], values=[]),
                "returns": True
            },
            {
                "name": "violates",
                "exp": List(elts=[], ctx=Load()),
                "returns": True
            }
        ]
        assign = Assign()
        assign.targets = [
            Tuple(
                elts=[Name(id=i['name'], ctx=Store()) for i in defs],
                ctx=Store()
            )
        ]
        assign.value = Tuple(
            elts=[i['exp'] for i in defs],
            ctx=Load()
        )
        rows.append(assign)
        rows.extend(self.rules)
        rows.append(Return(value=Tuple(
            elts=[Name(id=i['name'], ctx=Load()) for i in defs if i['returns']],
            ctx=Load()
        )))

        function_ast = FunctionDef(
            name="validator",
            args=arguments(
                args=[ast.arg(i) for i in self.args],
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
        # print(ast.dump(ast.parse(module_ast)))

        module_code = compile(module_ast, "<not_a_file>", "exec")
        function_code = [c for c in module_code.co_consts if isinstance(c, CodeType)][0]

#        return FunctionType(function_code, globals={'len': globals()['__builtins__']['len']})
        return FunctionType(function_code, globals={'__builtins__': {
            "len": len
        }})


if __name__ == "__main__":
    validator = Validator(args=['param'])
    validator.add_rule("integer", "param", "orders", name="my_orders", gt=20)
    validator.add_rule("string", "param", "items", min_length=3, max_length=5, default="1", convert="str")
    validator.add_rule("integer", "param", "limit", ge=0, default=0, convert="int")
    validation_handler = validator.build()

    import timeit

    NUMBER = 500_000

    # a = "a"
    # print("FUNC", timeit.timeit(lambda: len(a), number=NUMBER))
    # print("METHOD", timeit.timeit(lambda: a.__len__(), number=NUMBER))

    a = {
        "orders": 30,
        "items": b"403",
        "limit": 1,
        "items3": 40,
        "items4": 40,
        "items5": 40,
        "items6": 40,
        "items7": 40,
    }
    convertors = {
        "int": int,
        "str": lambda a: a.decode('utf-8') if type(a) == bytes else str(a),
        "bytes": lambda a: a.encode('utf-8') if type(a) == str else a
    }
    print(validation_handler(a, convert=convertors))
    print(a)

    base = timeit.timeit(lambda: 1, number=NUMBER)
    asted = timeit.timeit(lambda: validation_handler(a, convert=convertors), number=NUMBER) - base
    print("NEW (ast)", asted)

    from pydantic import BaseModel, validator, dataclasses

    @dataclasses.dataclass
    class ParamsDC:
        orders: int
        items: typing.Optional[int] = None
        limit: int = 1


    class Params(BaseModel):
        orders: int
        items: typing.Optional[int] = None
        limit: int = 1

        @validator("orders", pre=True, always=True)
        def set_orders(cls, v):
            if v <= 20:
                raise ValueError()
            return v

        @validator("items", pre=True, always=True)
        def set_items(cls, v):
            v = int(v)
            if v is not None and v <= 20:
                raise ValueError()
            return v

        @validator("limit", pre=True, always=True)
        def set_limit(cls, v):
            if v is None:
                return 0
            return int(v)

    #
    pydanted = timeit.timeit(lambda: Params.validate(a), number=NUMBER) - base
    print("Old (Pydantic metod)", pydanted)

    pydanted = timeit.timeit(lambda: Params(**a), number=NUMBER) - base
    print("Old (Pydantic model init", pydanted)
    #
    # pydanted = timeit.timeit(lambda: ParamsDC.validate(a), number=NUMBER) - base
    # print("Old (PydanticDC metod)", pydanted)
    #
    # pydanted = timeit.timeit(lambda: ParamsDC(**a), number=NUMBER) - base
    # print("Old (PydanticDC model init", pydanted)


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
