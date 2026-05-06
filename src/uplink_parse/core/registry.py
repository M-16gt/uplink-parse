from collections import defaultdict
from typing import Callable, Self
from uplink_parse.core.utils import _name
from uplink_parse.core._generics import RegistryGeneric, input_rt_func, output_rt_func


class BaseRegistry(RegistryGeneric[input_rt_func, output_rt_func]):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry = defaultdict(set)
        cls._registry_with_mro = defaultdict(set)
        cls.__name = _name(cls, "lower", replace=("_", ""))

    def __call__(self, func: Callable[[Self], input_rt_func]) -> Callable[[Self], input_rt_func]:
        self._registry[_name(func.__qualname__.split(".")[0])].add(func.__name__)
        return func

    @classmethod
    def get_registered(cls, owner: type | None = None, check_mro: bool = False,
                       passed_classes: set | None = None) -> set:
        if owner is None:
            return set().union(*cls._registry.values())

        owner_name = _name(owner)
        if not check_mro:
            return cls._registry[owner_name]

        if not cls._registry_with_mro[owner_name]:
            for base in (set(owner.__mro__) - (passed_classes or set())):
                cls._registry_with_mro[owner_name] |= cls._registry[_name(base)]

        return cls._registry_with_mro[owner_name]

    @classmethod
    def is_registered(cls, *names, owner: type | None = None, check_mro: bool = False) -> bool:
        return set(names).issubset(cls.get_registered(owner, check_mro=check_mro))
