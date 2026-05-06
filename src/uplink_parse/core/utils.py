def _name(obj, *attrs: str, **kwargs) -> str:
    name = obj if isinstance(obj, str) else obj.__name__
    for attr in attrs:
        name = getattr(name, attr)()
    for method_name, args in kwargs.items():
        method = getattr(name, method_name)
        if isinstance(args, (list, tuple)):
            name = method(*args)
        elif isinstance(args, dict):
            name = method(**args)
        else:
            name = method(args)

    return name
