import ast
import typing
from types import CodeType, FunctionType

from squall.validators.ast_helpers import append, call, getitem, setitem

Number = typing.Union[int, float]


class Validator:
    """Provides interface for building validation function.

    Example:
        ```
        >>> v = Validator(
        >>>     args=["param"],
        >>>     convertors={
        >>>         "int": int,
        >>>         "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a)
        >>>     }
        >>> )
        >>> v.add_rule("numeric", "param", "orders", name="my_orders", gt=20)
        >>> v.add_rule("string", "param", "name",
        >>>            min_length=3, max_length=5, default="anon", convert="str")
        >>> validator = v.build()
        >>> param = {"orders": 30, "name": b"Some", "useless1": 1, "useless2": 40}
        >>> validator(param)
        ({'my_orders': 30, 'name': 'Some'}, [])
        >>> param = {"orders": 20, "useless1": 1, "useless2": 40}
        >>> validator(param)
        ({'name': 'anon'}, [('param', 'orders', 'Validation error')])
    """

    def __init__(
        self,
        args: typing.List[str],
        convertors: typing.Dict[str, typing.Callable[..., typing.Any]],
    ) -> None:
        self.args = args
        assert len(self.args) > 0, "No input parameters names configured."
        self.convertors = convertors
        self.rules: typing.List[typing.Any] = []

    def add_rule(
        self,
        check: str,
        source: str,
        key: str,
        name: typing.Optional[str] = None,
        optional: bool = False,
        convert: typing.Optional[typing.Any] = None,
        default: typing.Optional[typing.Any] = None,
        # Numeric arguments
        gt: typing.Optional[Number] = None,
        ge: typing.Optional[Number] = None,
        lt: typing.Optional[Number] = None,
        le: typing.Optional[Number] = None,
        # String arguments
        min_length: typing.Optional[int] = None,
        max_length: typing.Optional[int] = None,
    ) -> None:
        """
        Adds new validation rule.

        :param check: type of check. At the moment two available `numeric`, `string`
        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param name: key name for results dict
        :param optional: allow None or key to be absent
        :param convert: convertor name. Must be defined during instance initialisation.
        :param default: default value to put if value is None or absent.
                        ATTN! There is no checks for defaults
        :param gt: Numeric only. Checked value should be grater than
        :param ge: Numeric only. Checked value should be grater than or equal
        :param lt: Numeric only. Checked value should be less than
        :param le: Numeric only. Checked value should be less than or equal
        :param min_length: String only. Checked value length should be more than or equal
        :param max_length: String only. Checked value length should be less than or equal
        """
        assert source in self.args
        name = name if name else key
        on_none: typing.List[typing.Union[ast.Expr, ast.Pass, ast.Assign]] = []
        if default is not None:
            on_none.append(setitem("results", name, ast.Constant(value=default)))
        else:
            on_none.append(
                ast.Pass()
                if optional
                else self.add_violate(source, key, "Can't be None")
            )
        rule: typing.Optional[typing.List[typing.Any]]

        if check == "numeric":
            rule = self.handle_numeric(source, key, name, gt=gt, ge=ge, lt=lt, le=le)
        elif check == "string":
            rule = self.handle_string(
                source, key, name, min_length=min_length, max_length=max_length
            )
        if rule is not None:
            if convert is not None:
                rule = [self.try_convert(source, key, convert, than=rule)]
            self.rules.append(self.if_none(source, key, on_none, rule))

    def try_convert(
        self, source: str, key: str, func: str, than: typing.Any
    ) -> ast.Try:
        """
        Builds code for conversion with try, except, else logic.
        In case of exception prevents further checks and writes violate record

        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param func: convertor function name. Must be defined during instance initialisation.
        :param than: code part for execution after success conversion
        """
        _try = ast.Try(finalbody=[], orelse=than)
        _try.handlers = [
            ast.ExceptHandler(
                body=[self.add_violate(source, key, f"Cast of `{func}` failed")]
            )
        ]
        _try.body = [
            setitem(
                entity_name=source,
                key=key,
                value=call(func, args=[getitem(source, ast.Constant(value=key))]),
            ),
        ]
        return _try

    def if_none(
        self,
        source: str,
        key: str,
        on_true: typing.List[typing.Any],
        on_false: typing.List[typing.Any],
    ) -> ast.If:
        """
        Builds following statement:
            ```
            if source.get(key) is None:
                on_true
            else:
                on_false
            ```
        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param on_true: list of expressions for execute if value is None
        :param on_false: list of expressions for execute if value is not None
        """
        return ast.If(
            test=ast.Compare(
                left=call(source, attribute="get", args=[ast.Constant(value=key)]),
                ops=[ast.Is()],
                comparators=[ast.Constant(value=None)],
            ),
            body=on_true,
            orelse=on_false,
        )

    @staticmethod
    def copy_to_results(source: str, key: str, name: str) -> ast.Assign:
        """
        Copy item value form source dict to results.
        Represents following code `results[name] = source[key]`

        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param name: results dict key name
        """
        return setitem(
            "results",
            key=name,
            value=getitem(entity_name=source, key=ast.Constant(value=key)),
        )

    def handle_numeric(
        self,
        source: str,
        key: str,
        name: str,
        gt: typing.Optional[Number] = None,
        ge: typing.Optional[Number] = None,
        lt: typing.Optional[Number] = None,
        le: typing.Optional[Number] = None,
    ) -> typing.Optional[typing.List[ast.If]]:
        """
        Numeric validator

        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param name: key name for results dict
        :param gt: value must be grater than
        :param ge: value must be grater than or equal
        :param lt: value must be less than
        :param le: value must be less than or equal
        """
        ops: typing.List[typing.Union[ast.Gt, ast.GtE]] = []
        comparators: typing.List[typing.Union[ast.Constant, ast.Subscript]] = []
        if lt is not None:
            comparators.append(ast.Constant(value=lt))
            ops.append(ast.Gt())
        elif le is not None:
            comparators.append(ast.Constant(value=le))
            ops.append(ast.GtE())

        comparators.append(getitem(source, ast.Constant(value=key)))

        if gt is not None:
            comparators.append(ast.Constant(value=gt))
            ops.append(ast.Gt())
        if ge is not None:
            comparators.append(ast.Constant(value=ge))
            ops.append(ast.GtE())

        if not ops:
            return None

        compare = ast.Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
        produce = self.copy_to_results(source, key, name)
        return [
            ast.If(
                test=ast.UnaryOp(op=ast.Not(), operand=compare),
                body=[self.add_violate(source, key, "Validation error")],
                orelse=[produce],
            )
        ]

    def handle_string(
        self,
        source: str,
        key: str,
        name: str,
        min_length: typing.Optional[int] = None,
        max_length: typing.Optional[int] = None,
    ) -> typing.Optional[typing.List[typing.Union[ast.If, ast.Assign]]]:
        """
        String validator

        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param name: key name for results dict
        :param min_length: value length must be grater than or equal
        :param max_length: value length must be less than or equal
        """
        get_length = ast.Assign(
            targets=[ast.Name(id=f"{name}_len", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="len", ctx=ast.Load()),
                args=[getitem(source, ast.Constant(value=key))],
                keywords=[],
            ),
        )

        ops: typing.List[typing.Union[ast.Gt, ast.GtE]] = []
        comparators: typing.List[typing.Union[ast.Constant, ast.Name]] = []
        if max_length is not None:
            comparators.append(ast.Constant(value=max_length))
            ops.append(ast.GtE())

        comparators.append(ast.Name(id=f"{name}_len", ctx=ast.Load()))

        if min_length is not None:
            comparators.append(ast.Constant(value=min_length))
            ops.append(ast.GtE())

        if not ops:
            return None

        compare = ast.Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
        produce = self.copy_to_results(source, key, name)
        return [
            get_length,
            ast.If(
                test=ast.UnaryOp(op=ast.Not(), operand=compare),
                body=[self.add_violate(source, key, "Validation error")],
                orelse=[produce],
            ),
        ]

    @staticmethod
    def add_violate(source: str, key: str, reason: str) -> ast.Expr:
        """Writes record to violations list

        Produce following code: `violates.append(source, key, reason)`
        Example:
            >>> add_violate('header', 'content-length', 'Cast of `int` failed')

        :param source: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param reason: violation reason
        """
        message = ast.Tuple(
            elts=[
                ast.Constant(value=source),
                ast.Constant(value=key),
                ast.Constant(value=reason),
            ],
            ctx=ast.Load(),
        )
        return append("violates", value=message)

    def build(self) -> FunctionType:
        """Builds validator function"""
        rows: typing.List[typing.Union[ast.Return, ast.Assign, ast.If]] = []
        defs = [
            {"name": "results", "exp": ast.Dict(keys=[], values=[]), "returns": True},
            {
                "name": "violates",
                "exp": ast.List(elts=[], ctx=ast.Load()),
                "returns": True,
            },
        ]
        assign = ast.Assign()
        assign.targets = [
            ast.Tuple(
                elts=[ast.Name(id=i["name"], ctx=ast.Store()) for i in defs],
                ctx=ast.Store(),
            )
        ]
        assign.value = ast.Tuple(elts=[i["exp"] for i in defs], ctx=ast.Load())
        rows.append(assign)
        rows.extend(self.rules)
        rows.append(
            ast.Return(
                value=ast.Tuple(
                    elts=[
                        ast.Name(id=i["name"], ctx=ast.Load())
                        for i in defs
                        if i["returns"]
                    ],
                    ctx=ast.Load(),
                )
            )
        )

        function_ast = ast.FunctionDef(
            name="validator",
            args=ast.arguments(
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
        module_ast = ast.Module(body=[function_ast], type_ignores=[])
        ast.fix_missing_locations(module_ast)

        module_code = compile(module_ast, "<not_a_file>", "exec")
        function_code = [c for c in module_code.co_consts if isinstance(c, CodeType)][0]

        return FunctionType(
            function_code, globals={"__builtins__": {"len": len, **self.convertors}}
        )
