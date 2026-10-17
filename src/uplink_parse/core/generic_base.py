from __future__ import annotations

import types
from collections.abc import Mapping
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin

from uplink_parse.core.exceptions import GenericConfigError

__all__ = ["GenericBase"]


def _name(t: Any) -> str:
    return getattr(t, "__name__", None) or getattr(t, "_name", None) or repr(t)


def _matches(value: Any, allowed: tuple[Any, ...]) -> bool:
    """Подходит ли подставленный тип под один из ``allowed``.

    Класс проверяется через ``issubclass``; параметризованный тип
    (``Literal["a"]``, ``list[int]``) сравнивается по своему ``origin``.
    """
    classes = tuple(a for a in allowed if isinstance(a, type))
    origin = get_origin(value)
    if origin is not None:
        return origin in allowed or (
            isinstance(origin, type) and issubclass(origin, classes)
        )
    return isinstance(value, type) and issubclass(value, classes)


class GenericBase:
    """Превращает параметры ``Generic[...]`` в ``config_types`` и проверяет их.

    ``config_types`` — «имя TypeVar -> подставленный тип». Как только класс
    полностью параметризован (в нём не осталось свободных TypeVar), он считается
    конкретным, и тогда:

    * все типовые параметры обязаны быть заданы;
    * значения проверяются по ``config_checks``: ``{имя_параметра: (Тип, ...)}``,
      подходит любой из перечисленных (``{"strategy": (Strategy,)}``,
      ``{"attr_name": (Literal,)}``). Таблицы наследуются и дополняются по MRO.

    Ошибка выбрасывается в момент определения класса, а не при первом вызове.
    """

    config_types: types.MappingProxyType[str, Any]
    config_checks: ClassVar[Mapping[str, tuple[Any, ...]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        config = dict(getattr(cls, "config_types", {}))

        for base in cls.__dict__.get("__orig_bases__", ()):
            origin = get_origin(base)
            if origin is None:
                continue
            args = get_args(base)

            if origin is Generic:
                config.update({a.__name__: a for a in args if isinstance(a, TypeVar)})
                continue

            params = getattr(origin, "__parameters__", ())
            if len(params) != len(args):
                continue

            subst = dict(zip(params, args, strict=True))
            config = {
                k: subst.get(v, v) if isinstance(v, TypeVar) else v
                for k, v in config.items()
            }

        cls.config_types = types.MappingProxyType(config)
        if not getattr(cls, "__parameters__", ()):
            cls._validate_config()

    @classmethod
    def _validate_config(cls) -> None:
        name = cls.__qualname__
        free = [n for n, t in cls.config_types.items() if isinstance(t, TypeVar)]
        if free:
            raise GenericConfigError(
                f"type parameters {free} are not specified; "
                f"parametrize the base class, e.g. Base[...]",
                source=name,
            )

        checks: dict[str, tuple[Any, ...]] = {}
        for klass in reversed(cls.__mro__):
            checks.update(vars(klass).get("config_checks", {}))

        for param, allowed in checks.items():
            if param not in cls.config_types:
                raise GenericConfigError(
                    f"type parameter {param!r} is required", source=name
                )
            if not _matches(cls.config_types[param], allowed):
                raise GenericConfigError(
                    f"type parameter {param!r}: expected "
                    f"{' | '.join(map(_name, allowed))}, "
                    f"got {cls.config_types[param]!r}",
                    source=name,
                )
