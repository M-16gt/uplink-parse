from __future__ import annotations

from typing import Any


class SingletonMeta(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> object:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    pass
