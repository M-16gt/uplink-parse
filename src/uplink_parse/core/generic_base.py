from types import MappingProxyType
from typing import Generic, TypeVarTuple, get_args

Ts = TypeVarTuple("Ts")


class GenericBase(Generic[*Ts]):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.config_types = {}
        for base in cls.__orig_bases__:  # noqa
            origin = getattr(base, "__origin__", None)
            if origin is None: continue
            cls.config_types.update({p.__name__: a for p, a in zip(origin.__parameters__, get_args(base))})
        cls.config_types = MappingProxyType(cls.config_types)