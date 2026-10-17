from typing import Any, cast

# from uplink_parse.core.utils.ctx import ctx

__all__ = [
    "to_list",
    "to_dict",
    "is_stateless",
]


def to_list(obj: Any) -> list[Any] | tuple[Any, ...]:
    if isinstance(obj, (list, tuple)):
        return obj
    return [obj] if obj is not None else []


def to_dict(obj: Any) -> dict[str, Any]:
    return obj if isinstance(obj, dict) else {}


def is_stateless(cls: Any) -> bool:
    init = cls.__init__
    if init is object.__init__:
        return True
    return cast(bool, init.__code__.co_argcount == 1)
