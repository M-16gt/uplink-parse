from __future__ import annotations

import types
from collections.abc import Mapping
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin

from uplink_parse.core.exceptions import GenericConfigError

__all__ = ["GenericBase"]


class GenericBase:
    

    def __init_subclass__(
    cls,
    *,
    check_typevars: tuple[str, ...] = (),
    **kwargs: Any,
) -> None:
    super().__init_subclass__(**kwargs)

    own_config: dict[str, Any] = {}

    for base in cls.__dict__.get("__orig_bases__", ()):
        origin = get_origin(base)
        if origin is None:
            continue

        params = getattr(origin, "__parameters__", ())
        args = get_args(base)

        if len(params) == len(args):
            own_config.update({
                param.__name__: arg
                for param, arg in zip(params, args, strict=False)
            })

    unresolved = [
        name for name in check_typevars
        if name not in own_config
        or isinstance(own_config[name], TypeVar)
    ]

    if unresolved:
        raise GenericConfigError(
            f"{cls.__name__} must explicitly define type variables: "
            f"{', '.join(unresolved)}"
        )

    config = dict(getattr(cls, "config_types", {}))
    config.update(own_config)
    cls.config_types = types.MappingProxyType(config)