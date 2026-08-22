import functools
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from typing_extensions import Self

from src.uplink_parse.core._generics import (
    RegistryGeneric,
    input_rt_func,
    output_rt_func,
)
from src.uplink_parse.core.utils import obj_name, to_list


class BaseRegistry(RegistryGeneric[input_rt_func, output_rt_func]):
    _registry: defaultdict[str, set[str]]
    _registry_with_mro: defaultdict[str, set[str]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._registry = defaultdict(set)
        cls._registry_with_mro = defaultdict(set)

    def __call__(
        self, func: Callable[[Self], input_rt_func] | None = None, hooks: Any = None
    ) -> Any:
        if func is None:
            return functools.partial(self, hooks=hooks)

        self._registry[obj_name(func.__qualname__.rsplit(".", maxsplit=1)[0])].add(
            func.__name__
        )

        for h in to_list(hooks):
            func = h(func)

        return func

    @classmethod
    def get_registered(
        cls,
        owner: type | None = None,
        check_mro: bool = False,
        passed_classes: set[str] | None = None,
    ) -> set[str]:
        if owner is None:
            return set().union(*cls._registry.values())

        owner_name = obj_name(owner)
        if not check_mro:
            return cls._registry[owner_name]

        if not cls._registry_with_mro[owner_name]:
            for base in set(owner.__mro__) - (passed_classes or set()):
                cls._registry_with_mro[owner_name] |= cls._registry[obj_name(base)]

        return cls._registry_with_mro[owner_name]

    @classmethod
    def is_registered(
        cls, *names: str, owner: type | None = None, check_mro: bool = False
    ) -> bool:
        return set(names).issubset(cls.get_registered(owner, check_mro=check_mro))
