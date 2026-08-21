from typing import Any

class SingletonMeta(type):
    _instances: dict[type, object]
    def __call__(cls, *args: Any, **kwargs: Any) -> object: ...

class Singleton(metaclass=SingletonMeta): ...
