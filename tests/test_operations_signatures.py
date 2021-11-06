import inspect

from squall import Router, Squall

method_names = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]
method_names = []


def test_signatures_consistency():
    base_sig = inspect.signature(Router.get)
    for method_name in method_names:
        router_method = getattr(Router, method_name)
        app_method = getattr(Squall, method_name)
        router_sig = inspect.signature(router_method)
        app_sig = inspect.signature(app_method)
        param: inspect.Parameter
        for key, param in base_sig.parameters.items():
            router_param: inspect.Parameter = router_sig.parameters[key]
            app_param: inspect.Parameter = app_sig.parameters[key]
            assert param.annotation == router_param.annotation
            assert param.annotation == app_param.annotation
            assert param.default == router_param.default
            assert param.default == app_param.default
