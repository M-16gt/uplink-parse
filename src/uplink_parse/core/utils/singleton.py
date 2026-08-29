from typing import Any, TypeVar, cast, overload

from uplink_parse.core.utils import is_stateless

T = TypeVar("T")

_instances: dict[type[Any], Any] = {}


def _get_instance(cls: type[T]) -> T:
    if cls not in _instances:
        if not is_stateless(cls):
            raise TypeError(f"{cls} must be stateless, not {cls.__name__}")
        _instances[cls] = cls()
    return cast(T, _instances[cls])


@overload
def get_instance(self_cls: type[T]) -> T: ...


@overload
def get_instance(self_cls: T) -> T: ...


def get_instance(self_cls: T | type[T]) -> T:
    if isinstance(self_cls, type):
        return _get_instance(self_cls)
    return _get_instance(type(self_cls))
