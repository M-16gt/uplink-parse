from typing import Any, ClassVar


def _make_hashable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return frozenset((k, _make_hashable(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return tuple(_make_hashable(v) for v in obj)
    if isinstance(obj, set):
        return frozenset(_make_hashable(v) for v in obj)
    try:
        hash(obj)
        return obj
    except TypeError:
        return id(obj)


class CachedMeta(type):
    _cache: ClassVar[dict[tuple[Any, ...], object]] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        key = (
            cls,
            tuple(_make_hashable(a) for a in args),
            _make_hashable(kwargs),
        )
        if key not in cls._cache:
            cls._cache[key] = super().__call__(*args, **kwargs)
        return cls._cache[key]


class Cached(metaclass=CachedMeta): ...
