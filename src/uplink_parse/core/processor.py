from abc import abstractmethod
from typing import Any

from uplink_parse.core.registry import BaseRegistry
from uplink_parse.core._generics import input_rt_func, output_rt_func
from uplink_parse.core.singleton import SingletonABC

class BaseProcessor(BaseRegistry[input_rt_func, output_rt_func], SingletonABC):
    """
    Базовый процессор, который находит зарегистрированные методы у объекта-владельца
    и заполняет ими целевой словарь (контекст).
    """

    @classmethod
    def process(
            cls,
            owner: Any,
            target: dict | None = None,
            **kwargs
    ) -> dict[str, Any]:
        """
        Основной метод запуска.

        :param owner: Экземпляр класса, у которого нужно вызвать зарегистрированные методы.
        :param target: Словарь, куда будут записаны результаты. Если None, создается новый.
        :return: Заполненный словарь target.
        """

        owner_class = owner.__class__
        if not hasattr(owner_class, "__func_names"):
            owner_class.__func_names = cls.get_registered(owner_class, **kwargs)

        return cls._populate_target(owner, owner_class.__func_names, target or {})

    @staticmethod
    @abstractmethod
    def _populate_target(
            owner: Any,
            func_names: set[str],
            target: dict
    ) -> dict:
        """
        Абстрактный метод реализации логики сбора данных.

        :param owner: Объект-владелец методов.
        :param func_names: Набор имен методов для вызова.
        :param target: Словарь для записи результатов.
        :return: Тот же словарь target после заполнения.

        Пример реализации:
            for name in func_names:
                method = getattr(owner, name)
                target[name] = method() if callable(method) else method
            return target
        """
        pass

def extract(owner: Any, target: dict | None = None, **kwargs) -> dict:
    for base in BaseProcessor.__subclasses__():
        target = base.process(owner, target, **kwargs)
    return target