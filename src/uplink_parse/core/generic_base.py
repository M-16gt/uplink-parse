import types
from typing import Any, Generic, get_args, get_origin


class GenericBase:
    config_types: types.MappingProxyType[str, Any]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        config = dict(getattr(cls, "config_types", {}))

        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is None:
                continue

            if origin is Generic:
                params = getattr(base, "__parameters__", ()) or getattr(
                    base, "__args__", ()
                )
            else:
                params = getattr(origin, "__parameters__", ())

            args = get_args(base)
            if not params or not args or len(params) != len(args):
                continue

            config.update({p.__name__: a for p, a in zip(params, args, strict=False)})

        cls.config_types = types.MappingProxyType(config)
