import ast
import typing
from types import CodeType, FunctionType

from squall.validators.ast_helpers import append, assign, call, getattribute, setitem

Number = typing.Union[int, float]


class Validator:
    """Provides interface for building validation function.

    Example:
        ```
        >>> v = Validator(
        >>>     args=["request"],
        >>>     convertors={
        >>>         "int": int,
        >>>         "str": lambda a: a.decode("utf-8") if type(a) == bytes else str(a)
        >>>     }
        >>> )
        >>> v.add_rule("path_params", "orders", check="numeric", name="my_orders", gt=20)
        >>> v.add_rule("path_params", "name", check="string",
        >>>            min_len=3, max_len=5, default="anon", convert="str")
        >>> validator = v.build()
        >>> param = {"orders": 30, "name": b"Some", "useless1": 1, "useless2": 40}
        >>> validator(request)
        ({'my_orders': 30, 'name': 'Some'}, [])
        >>> param = {"orders": 20, "useless1": 1, "useless2": 40}
        >>> validator(request)
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

        # self.getters used to build definitions of getters
        # ('headers', True) -> `headers_getlist = request.headers.getlist`
        # ('headers', False) -> `headers_get = request.headers.get`
        self.getters: typing.Set[typing.Tuple[str, bool]] = set()

    def add_rule(
        self,
        attribute: str,
        key: str,
        as_list: bool = False,
        check: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        convert: typing.Optional[typing.Any] = None,
        default: typing.Optional[typing.Any] = Ellipsis,
        # Numeric arguments
        gt: typing.Optional[Number] = None,
        ge: typing.Optional[Number] = None,
        lt: typing.Optional[Number] = None,
        le: typing.Optional[Number] = None,
        # String arguments
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
    ) -> None:
        """
        Adds new validation rule.

        :param check: type of check. At the moment two available `numeric`, `string`
        :param attribute: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param as_list: result expected as list
        :param name: key name for results dict
        :param convert: convertor name. Must be defined during instance initialisation.
        :param default: default value to put if value is None or absent.
                        ATTN! There is no checks for defaults
                        Ellipsis means field is mandatory
        :param gt: Numeric only. Checked value should be grater than
        :param ge: Numeric only. Checked value should be grater than or equal
        :param lt: Numeric only. Checked value should be less than
        :param le: Numeric only. Checked value should be less than or equal
        :param min_len: String only. Checked value length should be more than or equal
        :param max_len: String only. Checked value length should be less than or equal
        """
        self.getters.add((attribute, as_list))
        name = name or key
        assert (
            not convert or convert in self.convertors
        ), f"Convertor for {name} unknown"
        # Adds code: `candidate = <attribute>_<get|getlist>(key, Ellipsis)`
        getter = f"{attribute}_getlist" if as_list else f"{attribute}_get"
        args = [ast.Constant(value=key)]
        if not as_list:
            args.append(ast.Constant(value=Ellipsis))
        candidate_value = call(getter, args=args)
        self.rules.append(assign("candidate", candidate_value))

        save = setitem("results", name, ast.Name(id="candidate", ctx=ast.Load()))

        if check == "numeric":
            rule = self.validate_numeric(
                on_success=[save],
                on_failure=[self.add_violate(attribute, key, "Validation error")],
                gt=gt,
                ge=ge,
                lt=lt,
                le=le,
            )
        elif check == "string":
            rule = self.validate_string(
                on_success=[save],
                on_failure=[self.add_violate(attribute, key, "Validation error")],
                min_len=min_len,
                max_len=max_len,
            )
        else:
            rule = [save]

        checker = self.main_branching(
            default=default,
            on_undefined=[self.add_violate(attribute, key, f"Mandatory field missed")],
            on_default=[setitem("results", name, ast.Constant(value=default))],
            on_defined=[
                self.convert_candidate(
                    on_success=rule,
                    on_failure=[
                        self.add_violate(attribute, key, f"Cast of `{convert}` failed")
                    ],
                    func=convert,
                    as_list=as_list,
                )
            ],
        )

        self.rules.append(checker)

    @classmethod
    def convert_candidate(
        cls,
        on_success: typing.Any,
        on_failure: typing.Any,
        func: typing.Optional[str] = None,
        as_list: bool = False,
    ) -> ast.Try:
        """
        Builds code for conversion with try, except, else logic.
        In case of exception prevents further checks and writes violate record

        :param on_success: code part for execution after success conversion
        :param on_failure: code part for execution after conversion failed
        :param func: convertor function name. Must be defined during instance initialisation.
        :param as_list: should be cast func applied to each element in sequence
        """
        body: typing.List[typing.Union[ast.Pass, ast.Expr, ast.Call, ast.Assign]]
        expression: typing.Union[ast.Call, ast.Expr, ast.ListComp]
        if func is None:
            body = [ast.Pass()]
        else:
            if as_list:
                expression = cls.map(func, ast.Name(id="candidate", ctx=ast.Load()))
                body = [assign("candidate", value=expression)]
            else:
                expression = call(func, args=[ast.Name(id="candidate", ctx=ast.Load())])
                body = [assign("candidate", value=expression)]

        return ast.Try(
            body=body,
            handlers=[ast.ExceptHandler(body=on_failure)],
            orelse=on_success,
            finalbody=[],
        )

    @staticmethod
    def map(
        func: str, seq: typing.Union[ast.Call, ast.Subscript, ast.Name]
    ) -> ast.ListComp:
        """Map function to each sequence element and outputs result as a list.
        Generates the following code: `[func(i) for i in seq]`

        :param func: callable name
        :param seq: expression for get the sequence
        """
        return ast.ListComp(
            elt=call(func, args=[ast.Name(id="i", ctx=ast.Load())]),
            generators=[
                ast.comprehension(
                    target=ast.Name(id="i", ctx=ast.Store()),
                    iter=seq,
                    ifs=[],
                    is_async=0,
                )
            ],
        )

    @staticmethod
    def copy_to_results(attribute: str, key: str, name: str) -> ast.Assign:
        """
        Copy item value form source dict to results.
        Represents the following code `results[name] = source[key]`

        :param attribute: source dict name from validator parameters
        :param key: key of source dict to retrieve the checked value
        :param name: results dict key name
        """
        return setitem(
            "results",
            key=name,
            value=call(
                entity_name="request",
                attributes=[attribute, "get"],
                args=[ast.Constant(value=key), ast.Constant(value=Ellipsis)],
            ),
        )

    @staticmethod
    def validate_numeric(
        on_success: typing.List[typing.Any],
        on_failure: typing.List[typing.Any],
        gt: typing.Optional[Number] = None,
        ge: typing.Optional[Number] = None,
        lt: typing.Optional[Number] = None,
        le: typing.Optional[Number] = None,
    ) -> typing.List[typing.Any]:
        """
        Numeric validator

        :param on_success: statements for run if check is success
        :param on_failure: statements for run if check is fail
        :param gt: value must be grater than
        :param ge: value must be grater than or equal
        :param lt: value must be less than
        :param le: value must be less than or equal
        :returns: list of expressions for execution
        """
        ops: typing.List[typing.Union[ast.Gt, ast.GtE]] = []
        comparators: typing.List[typing.Union[ast.Constant, ast.Name]] = []
        if lt is not None:
            comparators.append(ast.Constant(value=lt))
            ops.append(ast.Gt())
        elif le is not None:
            comparators.append(ast.Constant(value=le))
            ops.append(ast.GtE())

        comparators.append(ast.Name(id="candidate", ctx=ast.Load()))

        if gt is not None:
            comparators.append(ast.Constant(value=gt))
            ops.append(ast.Gt())
        if ge is not None:
            comparators.append(ast.Constant(value=ge))
            ops.append(ast.GtE())

        if not ops:
            return on_success

        compare = ast.Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
        return [
            ast.If(
                test=compare,
                body=on_success,
                orelse=on_failure,
            )
        ]

    @staticmethod
    def validate_string(
        on_success: typing.List[typing.Any],
        on_failure: typing.List[typing.Any],
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
    ) -> typing.List[typing.Any]:
        """
        String validator

        :param on_success: statements for run if check is success
        :param on_failure: statements for run if check is fail
        :param min_len: value length must be grater than or equal
        :param max_len: value length must be less than or equal
        :returns: list of expressions for execution
        """
        ops: typing.List[typing.Union[ast.Gt, ast.GtE]] = []
        comparators: typing.List[
            typing.Union[ast.Constant, ast.Name, ast.Call, ast.Expr]
        ] = []

        if max_len is not None:
            comparators.append(ast.Constant(value=max_len))
            ops.append(ast.GtE())

        comparators.append(call("len", args=[ast.Name(id="candidate", ctx=ast.Load())]))

        if min_len is not None:
            comparators.append(ast.Constant(value=min_len))
            ops.append(ast.GtE())

        if not ops:
            return on_success

        compare = ast.Compare(left=comparators[0], ops=ops, comparators=comparators[1:])
        return [
            ast.If(
                test=compare,
                body=on_success,
                orelse=on_failure,
            ),
        ]

    @staticmethod
    def add_violate(attribute: str, name: str, reason: str) -> ast.Expr:
        """Writes record to violations list

        Produce following code: `violates.append(source, key, reason)`
        Example:
            >>> add_violate('headers','content-length', 'Cast of `int` failed')

        :param attribute: source attribute name
        :param name: target parameter name
        :param reason: violation reason
        """
        message = ast.Tuple(
            elts=[
                ast.Constant(value=attribute),
                ast.Constant(value=name),
                ast.Constant(value=reason),
                ast.Name(id="candidate", ctx=ast.Load()),
            ],
            ctx=ast.Load(),
        )
        return append("violates", value=message)

    @staticmethod
    def main_branching(
        default: typing.Any,
        on_undefined: typing.List[typing.Any],
        on_default: typing.List[typing.Any],
        on_defined: typing.List[typing.Any],
    ) -> ast.If:
        """The first line of making decision

        Generates following code:
            >>> if candidate == ... and default == ...:
            >>>    <on_undefined>
            >>> elif candidate == ...:
            >>>    <on_default>
            >>> else:
            >>>    <on_defined>
        """
        candidate = ast.Name(id="candidate", ctx=ast.Load())
        undefined = ast.Constant(value=Ellipsis)
        default = ast.Constant(value=default)
        candidate_cmp = ast.Compare(
            left=candidate, ops=[ast.Eq()], comparators=[undefined]
        )
        default_cmp = ast.Compare(left=default, ops=[ast.Eq()], comparators=[undefined])

        return ast.If(
            test=ast.BoolOp(op=ast.And(), values=[candidate_cmp, default_cmp]),
            body=on_undefined,
            orelse=[ast.If(test=candidate_cmp, body=on_default, orelse=on_defined)],
        )

    def build_getters(self) -> typing.List[ast.Assign]:
        """
        Builds definition of getters for reduce attribute lookups

        Example:
            >>> self.getters = {
            >>>     ('headers', True),
            >>>     ('path_params', False),
            >>>     ('query_params', True),
            >>> }
            Will generate following code
            >>> headers_getlist = request.headers.getlist
            >>> path_params_get = request.headers.get
            >>> query_params_getlist = request.query_params.getlist
        """
        assigns = []
        for attribute, as_list in self.getters:
            getter = "getlist" if as_list else "get"
            expr = assign(
                f"{attribute}_{getter}", getattribute("request", [attribute, getter])
            )
            assigns.append(expr)
        return assigns

    def build(self) -> FunctionType:
        """Builds validator function"""
        rows: typing.List[typing.Union[ast.Return, ast.Assign, ast.If]] = []
        rows.extend(self.build_getters())
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
            function_code,
            globals={"len": len, **self.convertors},
        )
