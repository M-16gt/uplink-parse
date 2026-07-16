from __future__ import annotations

class _SingletonBase:
    """База для всех singleton метаклассов."""

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)  # noqa
        return cls._instances[cls]

class SingletonMeta(_SingletonBase, type):
    """Singleton (для стратегий)."""
    pass


# Опционально: базовый класс для удобства
class Singleton(metaclass=SingletonMeta):
    """Базовый класс для singleton (если не нужны абстрактные методы)."""
    pass
