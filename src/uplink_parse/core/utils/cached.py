from typing import Any, ClassVar


class CachedMeta(type):
    _cache: ClassVar[dict[tuple[Any, ...], object]] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        key = (cls, args, frozenset(kwargs.items()))
        if key not in cls._cache:
            cls._cache[key] = super().__call__(*args, **kwargs)
        return cls._cache[key]


class Cached(metaclass=CachedMeta): ...
