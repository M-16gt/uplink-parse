from typing import Any

import attrs

# from src.uplink_parse.core.utils.ctx import ctx

__all__ = ["to_list", "obj_name", "transpose_dict_to_dataclass", "to_dict"]


def obj_name(obj: object) -> str:
    if isinstance(obj, str):
        return obj
    return (
        getattr(obj, "__qualname__", None)
        or getattr(obj, "__name__", type(obj).__name__)
        or ""
    )


def to_list(obj: Any) -> list[Any] | tuple[Any, ...]:
    if isinstance(obj, (list, tuple)):
        return obj
    return [obj] if obj is not None else []


def to_dict(obj: Any) -> dict[str, Any]:
    return obj if isinstance(obj, dict) else {}


def transpose_dict_to_dataclass(
    data: dict[str, list[Any]], cls: type[attrs.AttrsInstance]
) -> list[Any]:
    field_names = tuple(f.name for f in attrs.fields(cls))
    values_lists = tuple(data[name] for name in field_names)

    return [cls(*args) for args in zip(*values_lists, strict=True)]
