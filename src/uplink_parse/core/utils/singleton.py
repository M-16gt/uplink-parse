from functools import cache
from typing import TypeVar, cast

T = TypeVar("T")


@cache
def _get_instance(cls: type[T]) -> T:
    return cls()


def get_instance(self_cls: T | type[T]) -> T:
    return cast(
        T,
        _get_instance(self_cls if isinstance(self_cls, type) else type(self_cls)),  # type: ignore[arg-type]
    )
